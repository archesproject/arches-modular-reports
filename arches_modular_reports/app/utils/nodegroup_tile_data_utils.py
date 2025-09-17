import json
import operator
from functools import reduce
from uuid import UUID

from django.contrib.postgres.expressions import ArraySubquery
from django.db.models import (
    Case,
    Exists,
    F,
    Func,
    IntegerField,
    JSONField,
    OuterRef,
    Q,
    TextField,
    Value,
    When,
)
from django.db.models.expressions import CombinedExpression
from django.db.models.fields.json import KT
from django.db.models.functions import Cast, Concat, JSONObject
from django.urls import get_script_prefix, reverse
from django.utils.translation import gettext as _

from arches import VERSION as arches_version
from arches.app.models import models


class ArchesGetNodeDisplayValueV2(Func):
    function = "__arches_get_node_display_value_v2"
    output_field = TextField()
    arity = 3


class ArchesGetValueId(Func):
    function = "__arches_get_valueid"
    output_field = TextField()
    arity = 3


class ArrayToString(Func):
    function = "ARRAY_TO_STRING"
    output_field = TextField()
    arity = 3


def get_link(datatype, value_id):
    if datatype in ["concept", "concept-list"]:
        return reverse("rdm", args=[value_id])
    elif datatype in ["resource-instance", "resource-instance-list"]:
        return reverse("resource_report", args=[value_id])
    elif datatype in ["url"]:
        return value_id
    elif datatype in ["reference"]:
        return value_id["uri"]
    return ""


def build_valueid_annotation(data, is_user_rdm_admin, user_language):
    datatype = data.get("datatype", "")
    display_value = data.get("display_value")

    if datatype in ["concept", "resource-instance"]:
        value_ids = data.get("value_ids")
        if value_ids and (
            (datatype == "concept" and is_user_rdm_admin)
            or datatype == "resource-instance"
        ):
            return {
                "display_value": [
                    {
                        "label": display_value,
                        "link": get_link(datatype, value_ids),
                    }
                ],
                "has_links": True,
            }
        return {"display_value": display_value, "has_links": False}

    elif datatype in ["concept-list", "resource-instance-list", "reference"]:
        display_values = json.loads(data.get("display_value", "[]"))
        value_ids = data.get("value_ids", "[]") if data.get("value_ids", "[]") else []

        if datatype in ["concept-list", "resource-instance-list"]:
            value_ids = json.loads(value_ids)

        annotations = []
        if datatype == "concept-list" and not is_user_rdm_admin:
            return {"display_value": ", ".join(display_values), "has_links": False}
        else:
            for val_id, disp_val in zip(value_ids, display_values):
                if val_id:
                    annotations.append(
                        {
                            "label": disp_val,
                            "link": get_link(datatype, val_id),
                        }
                    )
            return {"display_value": annotations, "has_links": True}

    elif datatype in ["url"]:
        value_ids = data.get("value_ids")
        if value_ids:
            return {
                "display_value": [
                    {
                        "label": (
                            display_value
                            if display_value != ""
                            else get_link(datatype, value_ids)
                        ),
                        "link": get_link(datatype, value_ids),
                    }
                ],
                "has_links": True,
            }
        return {"display_value": display_value, "has_links": False}

    elif datatype == "file-list":
        file_tile_value = data.get("file_tile_value")

        def get_localized_metadata(file_info, key):
            nonlocal user_language
            if not (localized_values := file_info.get(key)):
                return None
            if not (value_for_lang := localized_values.get(user_language)):
                # todo(polish): handle variation in language regions.
                return list(localized_values.values)[0]["value"]
            return value_for_lang["value"]

        if file_tile_value:
            return {
                "display_value": display_value,
                "file_data": [
                    {
                        "file_id": file_info.get("file_id"),
                        "url": file_info.get("url"),
                        "title": get_localized_metadata(file_info, "title"),
                        "attribution": get_localized_metadata(file_info, "attribution"),
                        "description": get_localized_metadata(file_info, "description"),
                        "altText": get_localized_metadata(file_info, "altText"),
                    }
                    for file_info in file_tile_value
                ],
                "is_file": True,
            }
        return {"display_value": display_value, "has_links": False}

    return {"display_value": display_value, "has_links": False}


def annotate_related_graph_nodes_with_widget_labels(
    additional_nodes, related_graph, request_language
):
    return (
        models.Node.objects.filter(alias__in=additional_nodes, graph=related_graph)
        .exclude(datatype__in=["semantic", "annotation", "geojson-feature-collection"])
        .annotate(
            widget_label_json=(
                models.CardXNodeXWidget.objects.filter(node=OuterRef("nodeid")).values(
                    "label"
                )[:1]
            )
        )
        .annotate(widget_label=KT(f"widget_label_json__{request_language}"))
    )


def annotate_node_values(
    node_aliases, resourceinstance_id, permitted_nodegroups, user_language, tile_limit
):
    tile_subquery = (
        models.TileModel.objects.filter(
            resourceinstance=resourceinstance_id,
            nodegroup_id=OuterRef("nodegroup_id"),
        )
        .annotate(
            json_object=JSONObject(
                display_value=ArchesGetNodeDisplayValueV2(
                    F("data"),
                    OuterRef("nodeid"),
                    Value(user_language),
                ),
                tile_value=CombinedExpression(
                    F("data"),
                    "->",
                    Cast(OuterRef("nodeid"), output_field=TextField()),
                    output_field=JSONField(),
                ),
            ),
        )
        .exclude(json_object__display_value="")
        .exclude(json_object__tile_value=None)
        # This will work on Django 5.1+
        # .distinct("json_object__display_value", "sortorder")
        .order_by("sortorder")
        .values("json_object")
    )
    if tile_limit:
        tile_subquery = tile_subquery[:tile_limit]

    return (
        models.Node.objects.filter(
            alias__in=node_aliases,
            graph__resourceinstance__pk=resourceinstance_id,
            nodegroup__in=permitted_nodegroups,
        )
        .exclude(datatype__in=["semantic", "annotation", "geojson-feature-collection"])
        .annotate(display_data=ArraySubquery(tile_subquery))
    )


def get_sorted_filtered_tiles(
    *,
    resourceinstanceid,
    nodegroup_alias,
    sort_node_id,
    direction,
    query,
    user_language,
    user,
    filters,
):
    # semantic, annotation, and geojson-feature-collection data types are
    # excluded in __arches_get_node_display_value
    nodes = models.Node.objects.filter(
        graph__resourceinstance=resourceinstanceid,
        nodegroup__node__alias=nodegroup_alias,
        nodegroup__in=user.userprofile.viewable_nodegroups,
    ).exclude(
        datatype__in={"semantic", "annotation", "geojson-feature-collection"},
    )
    if arches_version >= (8, 0):
        nodes = nodes.filter(source_identifier=None)

    if not nodes:
        return models.TileModel.objects.none()

    field_annotations = {}
    alias_annotations = {}
    tile_filters = Q()

    for node in nodes:
        field_key = f'field_{str(node.pk).replace("-", "_")}'

        display_value = ArchesGetNodeDisplayValueV2(
            F("data"), Value(str(node.pk)), Value(user_language)
        )

        value_ids = None
        tile_value = None
        if (
            node.datatype == "concept"
            or node.datatype == "concept-list"
            or node.datatype == "resource-instance"
            or node.datatype == "resource-instance-list"
            or node.datatype == "url"
        ):
            value_ids = ArchesGetValueId(
                F("data"), Value(node.pk), Value(user_language)
            )
        elif node.datatype == "file-list":
            tile_value = F(f"data__{node.pk}")
        elif node.datatype == "reference":
            value_ids = F(f"data__{node.pk}")

        field_annotations[field_key] = display_value
        alias_annotations[node.alias] = JSONObject(
            display_value=display_value,
            datatype=Value(node.datatype),
            value_ids=value_ids,
            file_tile_value=tile_value,
        )
        if filters:
            for filter in filters:
                if node.alias == filter["alias"]:
                    tile_filters &= Q(
                        **{
                            f"data__{node.pk}__{filter['field_lookup']}": filter[
                                "value"
                            ]
                        }
                    )

    # adds spaces between fields
    display_values_with_spaces = []
    for field in [F(field) for field in field_annotations.keys()]:
        display_values_with_spaces.append(field)
        display_values_with_spaces.append(Value(" "))

    tiles = (
        models.TileModel.objects.filter(
            resourceinstance_id=resourceinstanceid, nodegroup_id=nodes[0].nodegroup_id
        )
        .annotate(**field_annotations)
        .annotate(alias_annotations=JSONObject(**alias_annotations))
        .annotate(
            search_text=Concat(*display_values_with_spaces, output_field=TextField())
        )
        .filter(tile_filters & Q(search_text__icontains=query))
        .annotate(
            has_children=Exists(
                models.TileModel.objects.filter(parenttile=OuterRef("pk"))
            )
        )
    )

    if sort_node_id:
        sort_field_name = f'field_{sort_node_id.replace("-", "_")}'

        sort_priority = Case(
            When(**{f"{sort_field_name}__isnull": True}, then=Value(1)),
            When(**{f"{sort_field_name}": ""}, then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        )

        if direction.lower().startswith("asc"):
            tiles = tiles.annotate(sort_priority=sort_priority).order_by(
                "sort_priority", F(sort_field_name).asc()
            )
        else:
            tiles = tiles.annotate(sort_priority=sort_priority).order_by(
                "-sort_priority", F(sort_field_name).desc()
            )
    else:
        # default sort order for consistent pagination
        tiles = tiles.order_by("sortorder")

    return tiles


def get_sorted_filtered_relations(
    *,
    resource,
    related_graph,
    nodes,
    permitted_nodegroups,
    sort_field,
    direction,
    query,
    request_language,
):
    if arches_version < (8, 0):
        resource_from_field = "resourceinstanceidfrom"
        resource_from_graph_field = "resourceinstancefrom_graphid"
        resource_to_field = "resourceinstanceidto"
        resource_to_graph_field = "resourceinstanceto_graphid"
        node_field = "nodeid"
    else:
        resource_from_field = "from_resource"
        resource_from_graph_field = "from_resource_graph"
        resource_to_field = "to_resource"
        resource_to_graph_field = "to_resource_graph"
        node_field = "node"

    def make_tile_annotations(node, direction):
        resource_field = resource_to_field if direction == "to" else resource_from_field
        tile_query = ArraySubquery(
            models.TileModel.objects.filter(
                resourceinstance=OuterRef(resource_field),
                nodegroup_id=node.nodegroup_id,
            )
            .exclude(**{f"data__{node.pk}__isnull": True})
            .annotate(
                display_value=ArchesGetNodeDisplayValueV2(
                    F("data"), Value(node.pk), Value(request_language)
                )
            )
            .order_by("sortorder")
            .values("display_value")
            .distinct()
        )
        return ArrayToString(
            tile_query,
            Value(", "),  # delimiter
            Value(_("None")),  # null replacement
        )

    def make_tile_instance_details_annotations(node, direction):
        resource_field = resource_to_field if direction == "to" else resource_from_field
        return ArraySubquery(
            models.TileModel.objects.filter(
                resourceinstance=OuterRef(resource_field),
                nodegroup_id=node.nodegroup_id,
            )
            .exclude(**{f"data__{node.pk}__isnull": True})
            .order_by("sortorder")
            .annotate(node_value=F(f"data__{node.pk}"))
            .values("node_value")
            .distinct()
        )

    data_annotations = {
        node.alias: Case(
            When(
                Q(**{resource_from_field: resource}),
                then=make_tile_annotations(node, "to"),
            ),
            When(
                Q(**{resource_to_field: resource}),
                then=make_tile_annotations(node, "from"),
            ),
        )
        for node in nodes
        if node.nodegroup_id in permitted_nodegroups
    }
    instance_details_annotations = {
        node.alias
        + "_instance_details": Case(
            When(
                Q(**{resource_from_field: resource}),
                then=make_tile_instance_details_annotations(node, "to"),
            ),
            When(
                Q(**{resource_to_field: resource}),
                then=make_tile_instance_details_annotations(node, "from"),
            ),
        )
        for node in nodes
        if node.datatype
        in {
            "concept",
            "concept-list",
            "resource-instance",
            "resource-instance-list",
            "url",
            "file-list",
        }
        and node.nodegroup_id in permitted_nodegroups
    }

    relations = (
        (
            models.ResourceXResource.objects.filter(
                Q(**{resource_from_field: resource}),
                Q(**{resource_to_graph_field: related_graph}),
                Q(**{f"{node_field}__nodegroup_id__in": permitted_nodegroups}),
            )
            | models.ResourceXResource.objects.filter(
                Q(**{resource_to_field: resource}),
                Q(**{resource_from_graph_field: related_graph}),
                Q(**{f"{node_field}__nodegroup_id__in": permitted_nodegroups}),
            )
        )
        .distinct()
        .annotate(
            relation_name_json=(
                models.CardXNodeXWidget.objects.filter(
                    node=OuterRef(node_field)
                ).values("label")[:1]
            )
        )
        # TODO: add fallback to system language? Below also.
        # https://github.com/archesproject/arches/issues/10028
        .annotate(**{"@relation_name": KT(f"relation_name_json__{request_language}")})
        .annotate(
            display_name_json=Case(
                When(
                    Q(**{resource_from_field: resource}),
                    then=F(f"{resource_to_field}__name"),
                ),
                When(
                    Q(**{resource_to_field: resource}),
                    then=F(f"{resource_from_field}__name"),
                ),
            )
        )
        .annotate(**{"@display_name": KT(f"display_name_json__{request_language}")})
        .annotate(**data_annotations)
        .annotate(**instance_details_annotations)
    )

    if query:
        # OR Q objects together to allow matching any annotation.
        all_filters = reduce(
            operator.or_,
            [
                Q(**{"@relation_name__icontains": query}),
                Q(**{"@display_name__icontains": query}),
                *[
                    Q(**{f"{annotation}__icontains": query})
                    for annotation in data_annotations
                ],
            ],
        )
        relations = relations.filter(all_filters)

    if direction.lower().startswith("asc"):
        relations = relations.order_by(F(sort_field).asc(nulls_last=True))
    else:
        relations = relations.order_by(F(sort_field).desc(nulls_last=True))

    return relations


def filter_hidden_nodes(
    list_or_dict_to_filter, card_visibility_reference, node_visibility_reference
):
    if isinstance(list_or_dict_to_filter, list):
        return [
            filter_hidden_nodes(
                item, card_visibility_reference, node_visibility_reference
            )
            for item in list_or_dict_to_filter
        ]
    if isinstance(list_or_dict_to_filter, dict):
        dict_to_filter = {**list_or_dict_to_filter}
        for key, val in dict_to_filter.items():
            if isinstance(val, dict) and "@node_id" in val:
                if not card_visibility_reference.get(
                    val["@node_id"], True
                ) or not node_visibility_reference.get(val["@node_id"], True):
                    dict_to_filter[key] = None
                else:
                    dict_to_filter[key] = filter_hidden_nodes(
                        val, card_visibility_reference, node_visibility_reference
                    )
        return dict_to_filter
    raise TypeError


def prepare_links(
    node,
    tile_values,
    node_display_value,
    request_language,
    value_finder,
    is_user_rdm_admin,
):
    links = []

    ### TEMPORARY HELPERS

    def get_resource_labels(tiledata):
        """This is a source of N+1 queries, but we're working around the fact
        that __arches_get_node_display_value() is lossy, i.e. if the display
        values contain the delimiter (", ") we can't distinguish those.
        So we just get the display values again, unfortunately.
        TODO: graduate from the PG function to ORM expressions?
        """
        nonlocal request_language
        ordered_ids = [UUID(innerTileVal["resourceId"]) for innerTileVal in tiledata]
        resources = models.ResourceInstance.objects.filter(pk__in=ordered_ids).in_bulk()
        return [
            (
                resources[res_id]
                .descriptors.get(request_language, {})
                .get("name", _("Undefined"))
                if res_id in resources
                else _("Undefined")
            )
            for res_id in ordered_ids
        ]

    def get_concept_labels(value_ids):
        nonlocal value_finder
        return [
            value_finder.get_value(value_id_str).value for value_id_str in value_ids
        ]

    def get_concept_ids(value_ids):
        nonlocal value_finder
        return [
            value_finder.get_value(value_id_str).concept_id
            for value_id_str in value_ids
        ]

    def form_file_url(tile_url_string):
        prefix = get_script_prefix()
        if tile_url_string.startswith("http") or tile_url_string.startswith(prefix):
            return tile_url_string
        url = get_script_prefix() + tile_url_string
        return url.replace("//", "/")

    ### BEGIN LINK GENERATION
    for tile_val in tile_values:
        if tile_val:
            match node.datatype:
                case "resource-instance":
                    links.append(
                        {
                            "label": node_display_value,
                            "link": get_link(node.datatype, tile_val[0]["resourceId"]),
                        }
                    )
                case "resource-instance-list":
                    labels = get_resource_labels(tile_val)
                    for related_resource, label in zip(tile_val, labels, strict=True):
                        links.append(
                            {
                                "label": label,
                                "link": get_link(
                                    node.datatype, related_resource["resourceId"]
                                ),
                            }
                        )
                case "concept":
                    if is_user_rdm_admin and (
                        concept_id_results := get_concept_ids([tile_val])
                    ):
                        links.append(
                            {
                                "label": node_display_value,
                                "link": get_link(node.datatype, concept_id_results[0]),
                            }
                        )
                case "concept-list":
                    if is_user_rdm_admin:
                        concept_ids = get_concept_ids(tile_val)
                        labels = get_concept_labels(tile_val)
                        for concept_id, label in zip(concept_ids, labels, strict=True):
                            links.append(
                                {
                                    "label": label,
                                    "link": get_link(node.datatype, concept_id),
                                }
                            )
                case "url":
                    links.append(
                        {
                            "label": (
                                tile_val["url_label"]
                                if tile_val["url_label"]
                                else tile_val["url"]
                            ),
                            "link": tile_val["url"],
                        }
                    )
                case "file-list":
                    for file in tile_val:
                        links.append(
                            {
                                "is_file": True,
                                "altText": file.get("altText", {}).get(
                                    request_language
                                )["value"],
                                "attribution": file.get("attribution", {}).get(
                                    request_language
                                )["value"],
                                "title": file.get("title", {}).get(
                                    request_language, ""
                                )["value"],
                                "description": file.get("description", {}).get(
                                    request_language, ""
                                )["value"],
                                "url": form_file_url(file["url"]),
                            }
                        )
                case "reference":
                    for val_id, disp_val in zip(
                        tile_val, json.loads(node_display_value)
                    ):
                        if val_id:
                            links.append(
                                {
                                    "label": disp_val,
                                    "link": get_link(node.datatype, val_id),
                                }
                            )

    return links


def is_number(s):
    try:
        float(s)
        return True
    except:
        return False


def array_from_string(input_str):
    if not input_str:
        return []
    elif is_number(input_str):
        return [input_str]
    else:
        try:
            return json.loads(input_str)
        except json.JSONDecodeError:
            return [input_str]
