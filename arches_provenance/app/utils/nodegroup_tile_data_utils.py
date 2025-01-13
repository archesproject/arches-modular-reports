from django.db.models import (
    Case,
    F,
    FilteredRelation,
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
from django.db.models.functions import Concat, JSONObject, NullIf

from arches.app.models import models
from arches.app.models.tile import Tile

from arches_provenance.app.utils.label_based_graph_with_branch_export import (
    LabelBasedGraphWithBranchExport,
)


class ArchesGetNodeDisplayValue(Func):
    function = "__arches_get_node_display_value_v2"
    output_field = TextField()
    arity = 3


def get_sorted_filtered_tiles(
    *, resourceinstanceid, nodegroupid, sort_node_id, sort_order, query, user_language
):
    # semantic, annotation, and geojson-feature-collection data types are
    # excluded in __arches_get_node_display_value
    nodes = models.Node.objects.filter(nodegroup_id=nodegroupid).exclude(
        datatype__in=["semantic", "annotation", "geojson-feature-collection"]
    )

    field_annotations = {}
    alias_annotations = {}

    for node in nodes:
        field_key = f'field_{str(node.pk).replace("-", "_")}'

        display_value = ArchesGetNodeDisplayValue(
            F("data"), Value(str(node.pk)), Value(user_language)
        )

        field_annotations[field_key] = display_value
        alias_annotations[node.alias] = JSONObject(
            display_value=display_value, datatype=Value(node.datatype)
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

        if sort_order == "asc":
            tiles = tiles.annotate(sort_priority=sort_priority).order_by(
                "sort_priority", F(sort_field_name).asc()
            )
        elif sort_order == "desc":
            tiles = tiles.annotate(sort_priority=sort_priority).order_by(
                "-sort_priority", F(sort_field_name).desc()
            )
    else:
        # default sort order for consistent pagination
        tiles = tiles.order_by("sortorder")

    return tiles


def get_sorted_filtered_relations(
    *, resource, related_graphid, nodes, sort, direction, request_language
):
    for node in nodes:
        # View should have already checked and raised JSONErrorResponse.
        assert node.nodegroup.cardinality == "1"
    to_tile_annotations = {
        node.alias
        + "_to_tile": FilteredRelation(
            "resourceinstanceidto__tilemodel",
            condition=Q(
                resourceinstanceidto__tilemodel__nodegroup_id=node.nodegroup_id,
            ),
        )
        for node in nodes
    }
    from_tile_annotations = {
        node.alias
        + "_from_tile": FilteredRelation(
            "resourceinstanceidfrom__tilemodel",
            condition=Q(
                resourceinstanceidfrom__tilemodel__nodegroup_id=node.nodegroup_id,
            ),
        )
        for node in nodes
    }
    data_annotations = {
        node.alias: NullIf(
            Case(
                When(
                    Q(resourceinstanceidfrom=resource),
                    then=ArchesGetNodeDisplayValue(
                        F(node.alias + "_to_tile__data"),
                        Value(node.pk),
                        Value(request_language),
                    ),
                ),
                When(
                    Q(resourceinstanceidto=resource),
                    then=ArchesGetNodeDisplayValue(
                        F(node.alias + "_from_tile__data"),
                        Value(node.pk),
                        Value(request_language),
                    ),
                ),
            ),
            Value("", output_field=TextField()),
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
        .annotate(
            widget_label_json=Subquery(
                models.CardXNodeXWidget.objects.filter(node=OuterRef("nodeid"))
                .order_by("sortorder")
                .values("label")[:1]
            )
        )
        .annotate(widget_label=KT(f"widget_label_json__{request_language}"))
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
        .annotate(display_name=KT(f"display_name_json__{request_language}"))
        .annotate(**from_tile_annotations)
        .annotate(**to_tile_annotations)
        .annotate(**data_annotations)
    )

    if direction.startswith("asc"):
        relations = relations.order_by(F(sort).asc(nulls_last=True))
    else:
        relations = relations.order_by(F(sort).desc(nulls_last=True))

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
