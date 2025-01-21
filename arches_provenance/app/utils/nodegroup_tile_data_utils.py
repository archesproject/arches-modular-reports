import json
import operator
from functools import reduce

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
from django.utils.translation import gettext as _

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
        return ArrayToString(
            ArraySubquery(
                models.TileModel.objects.filter(
                    resourceinstance=OuterRef(f"resourceinstanceid{direction}"),
                    nodegroup_id=node.nodegroup_id,
                )
                .exclude(**{f"data__{node.pk}__isnull": True})
                .annotate(
                    display_value=ArchesGetNodeDisplayValue(
                        F("data"), Value(node.pk), Value(request_language)
                    )
                )
                .order_by("sortorder")
                .values("display_value")
                .distinct()  # TODO: parameterize this?
            ),
            Value(", "),  # delimiter
            Value(_("None")),  # null replacement
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
