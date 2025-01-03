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
from django.db.models.functions import Concat
from django.utils.translation import gettext as _

from arches.app.models import models
from arches.app.models.tile import Tile

from arches_provenance.app.utils.label_based_graph_with_branch_export import (
    LabelBasedGraphWithBranchExport,
)


class ArchesGetNodeDisplayValue(Func):
    function = "__arches_get_node_display_value"
    output_field = TextField()
    arity = 3


class ArrayToString(Func):
    function = "ARRAY_TO_STRING"
    output_field = TextField()
    arity = 3


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
    *, resourceinstanceid, nodegroupid, sort_node_id, sort_order, query, user_language
):
    # semantic, annotation, and geojson-feature-collection data types are excluded in __arches_get_node_display_value
    nodes = models.Node.objects.filter(nodegroup_id=nodegroupid).exclude(
        datatype__in=["semantic", "annotation", "geojson-feature-collection"]
    )

    annotations = {
        f'field_{str(node.pk).replace("-", "_")}': ArchesGetNodeDisplayValue(
            F("data"), Value(str(node.pk)), Value(user_language)
        )
        for node in nodes
    }

    # adds spaces between fields
    display_values_with_spaces = []
    for field in [F(field) for field in annotations.keys()]:
        display_values_with_spaces.append(field)
        display_values_with_spaces.append(Value(" "))

    tiles = (
        Tile.objects.filter(
            resourceinstance_id=resourceinstanceid, nodegroup_id=nodegroupid
        )
        .annotate(**annotations)
        .annotate(
            search_text=Concat(*display_values_with_spaces, output_field=TextField())
        )
        .filter(search_text__icontains=query)
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
                # TODO: consider distinct, especially for concept values.
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
                Q(resourceinstanceidfrom=resource),
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
