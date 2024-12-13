from django.db.models.functions import Concat
from django.db.models import (
    Case,
    F,
    Func,
    IntegerField,
    TextField,
    Value,
    When,
)

from arches.app.models import models
from arches.app.models.tile import Tile


class ArchesGetNodeDisplayValue(Func):
    function = "__arches_get_node_display_value"
    output_field = TextField()
    arity = 3


def get_sorted_filtered_tiles(
    resourceinstanceid, nodegroupid, sort_node_id, sort_order, query, user_language
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
        tiles = tiles.order_by(
            "sortorder"
        )  # default sort order for consistent pagination

    return tiles
