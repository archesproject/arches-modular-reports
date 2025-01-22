import json
import operator
from functools import reduce
from uuid import UUID

from django.contrib.postgres.expressions import ArraySubquery
from django.db.models import (
    Case,
    F,
    Func,
    IntegerField,
    OuterRef,
    Q,
    Subquery,
    TextField,
    Value,
    When,
)
from django.db.models.fields.json import KT
from django.db.models.functions import Concat, JSONObject
from django.urls import reverse
from django.db.models.functions import Concat
from django.urls import reverse
from django.utils.translation import gettext as _

from arches.app.datatypes.concept_types import BaseConceptDataType
from arches.app.models import models
from arches.app.models.tile import Tile

from arches_provenance.app.utils.label_based_graph_with_branch_export import (
    LabelBasedGraphWithBranchExport,
)


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
    return ""


def build_valueid_annotation(data):
    datatype = data.get("datatype", "")
    display_value = data.get("display_value")

    if datatype in ["concept", "resource-instance"]:
        value_ids = data.get("value_ids")
        if value_ids:
            return {
                "display_value": [
                    {
                        "label": display_value,
                        "link": get_link(datatype, value_ids),
                    }
                ]
            }
        return {"display_value": display_value}

    elif datatype in ["concept-list", "resource-instance-list"]:
        value_ids = json.loads(data.get("value_ids", "[]"))
        display_values = json.loads(data.get("display_value", "[]"))

        annotations = []
        for val_id, disp_val in zip(value_ids, display_values):
            if val_id:
                annotations.append(
                    {
                        "label": disp_val,
                        "link": get_link(datatype, val_id),
                    }
                )
        return {"display_value": annotations}

    return {"display_value": display_value}


def annotate_related_graph_nodes_with_widget_labels(
    additional_nodes, related_graphid, request_language
):
    return (
        models.Node.objects.filter(alias__in=additional_nodes, graph_id=related_graphid)
        .exclude(datatype__in=["semantic", "annotation", "geojson-feature-collection"])
        .annotate(
            widget_label_json=Subquery(
                models.CardXNodeXWidget.objects.filter(node=OuterRef("nodeid"))
                .order_by("sortorder")
                .values("label")[:1]
            )
        )
        .annotate(widget_label=KT(f"widget_label_json__{request_language}"))
    )


def get_sorted_filtered_tiles(
    *, resourceinstanceid, nodegroupid, sort_node_id, direction, query, user_language
):
    # semantic, annotation, and geojson-feature-collection data types are
    # excluded in __arches_get_node_display_value
    nodes = models.Node.objects.filter(nodegroup_id=nodegroupid).exclude(
        datatype__in=["semantic", "annotation", "geojson-feature-collection"]
    )

    if not nodes:
        return Tile.objects.none()

    field_annotations = {}
    alias_annotations = {}

    for node in nodes:
        field_key = f'field_{str(node.pk).replace("-", "_")}'

        display_value = ArchesGetNodeDisplayValueV2(
            F("data"), Value(str(node.pk)), Value(user_language)
        )

        value_ids = None
        if (
            node.datatype == "concept"
            or node.datatype == "concept-list"
            or node.datatype == "resource-instance"
            or node.datatype == "resource-instance-list"
        ):
            value_ids = ArchesGetValueId(
                F("data"), Value(node.pk), Value(user_language)
            )

        field_annotations[field_key] = display_value
        alias_annotations[node.alias] = JSONObject(
            display_value=display_value,
            datatype=Value(node.datatype),
            value_ids=value_ids,
        )

    # adds spaces between fields
    display_values_with_spaces = []
    for field in [F(field) for field in field_annotations.keys()]:
        display_values_with_spaces.append(field)
        display_values_with_spaces.append(Value(" "))

    tiles = (
        Tile.objects.filter(
            resourceinstance_id=resourceinstanceid, nodegroup_id=nodegroupid
        )
        .annotate(**field_annotations)
        .annotate(alias_annotations=JSONObject(**alias_annotations))
        .annotate(
            search_text=Concat(*display_values_with_spaces, output_field=TextField())
        )
        .filter(search_text__icontains=query)
        .prefetch_related("tilemodel_set")
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

    for tile in tiles:
        new_alias_annotations = {}

        for key, data in tile.alias_annotations.items():
            new_alias_annotations[key] = build_valueid_annotation(data)

        tile.alias_annotations = new_alias_annotations

    return tiles


def get_sorted_filtered_relations(
    *, resource, related_graphid, nodes, sort_field, direction, query, request_language
):
    def make_tile_annotations(node, direction):
        tile_query = ArraySubquery(
            models.TileModel.objects.filter(
                resourceinstance=OuterRef(f"resourceinstanceid{direction}"),
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
        return ArraySubquery(
            models.TileModel.objects.filter(
                resourceinstance=OuterRef(f"resourceinstanceid{direction}"),
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
                Q(resourceinstanceidfrom=resource),
                then=make_tile_annotations(node, "to"),
            ),
            When(
                Q(resourceinstanceidto=resource),
                then=make_tile_annotations(node, "from"),
            ),
        )
        for node in nodes
    }
    instance_details_annotations = {
        node.alias
        + "_instance_details": Case(
            When(
                Q(resourceinstanceidfrom=resource),
                then=make_tile_instance_details_annotations(node, "to"),
            ),
            When(
                Q(resourceinstanceidto=resource),
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
        }
    }

    relations = (
        (
            models.ResourceXResource.objects.filter(
                resourceinstanceidfrom=resource,
                resourceinstanceto_graphid=related_graphid,
            )
            | models.ResourceXResource.objects.filter(
                resourceinstanceidto=resource,
                resourceinstancefrom_graphid=related_graphid,
            )
        )
        .distinct()
        .annotate(
            relation_name_json=Subquery(
                models.CardXNodeXWidget.objects.filter(node=OuterRef("nodeid"))
                .order_by("sortorder")
                .values("label")[:1]
            )
        )
        # TODO: add fallback to system language? Below also.
        # https://github.com/archesproject/arches/issues/10028
        .annotate(**{"@relation_name": KT(f"relation_name_json__{request_language}")})
        .annotate(
            display_name_json=Case(
                When(
                    Q(resourceinstanceidfrom=resource),
                    then=F(f"resourceinstanceidto__name"),
                ),
                When(
                    Q(resourceinstanceidto=resource),
                    then=F(f"resourceinstanceidfrom__name"),
                ),
            )
        )
        .annotate(**{"@display_name": KT(f"display_name_json__{request_language}")})
        .annotate(**data_annotations)
        .annotate(**instance_details_annotations)
    )

    if query:
        # OR (|) Q() objects together to allow matching any annotation.
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


def serialize_tiles_with_children(tile, serialized_graph):
    node_ids = list(tile.data.keys())

    if str(tile.nodegroup_id) not in node_ids:
        node_ids.append(str(tile.nodegroup_id))

    node_ids_to_tiles_reference = {}
    for node_id in node_ids:
        tile_list = node_ids_to_tiles_reference.get(node_id, [])
        tile_list.append(tile)
        node_ids_to_tiles_reference[node_id] = tile_list

    tile._children = [
        serialize_tiles_with_children(child, serialized_graph)
        for child in tile.tilemodel_set.order_by("sortorder")
    ]

    return {
        "@children": tile._children,
        **LabelBasedGraphWithBranchExport.from_tile(
            tile, node_ids_to_tiles_reference, {}, serialized_graph=serialized_graph
        ),
    }


def prepare_links(annotated_relation, node, request_language):
    links = []

    ### TEMPORARY HELPERS
    value_finder = BaseConceptDataType()  # fetches serially, but has a cache

    def get_resource_labels(tiledata):
        """This is a source of N+1 queries, but we're working around the fact
        that __arches_get_node_display_value() is lossy, i.e. if the display
        values contain the delimiter (", ") we can't distinguish those.
        So we just get the display values again, unfortunately.

        TODO: graduate from the PG function to ORM expressions?
        """
        nonlocal request_language
        ordered_ids = [innerTileVal["resourceId"] for innerTileVal in tiledata]
        resources = models.ResourceInstance.objects.filter(pk__in=ordered_ids).in_bulk()
        return [
            resources[UUID(res_id)]
            .descriptors.get(request_language, {})
            .get("name", _("Undefined"))
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

    ### BEGIN LINK GENERATION

    tile_vals = (
        getattr(annotated_relation, node.alias + "_instance_details", None) or []
    )
    for tile_val in tile_vals:
        match node.datatype:
            case "resource-instance":
                links.append(
                    {
                        "label": getattr(annotated_relation, node.alias),
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
                if concept_id_results := get_concept_ids([tile_val]):
                    links.append(
                        {
                            "label": getattr(annotated_relation, node.alias),
                            "link": get_link(node.datatype, concept_id_results[0]),
                        }
                    )
            case "concept-list":
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
                        "label": tile_val["url_label"],
                        "link": tile_val["url"],
                    }
                )

    return links
