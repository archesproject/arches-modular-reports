import json

from django.db.models import (
    Case,
    Exists,
    F,
    Func,
    IntegerField,
    OuterRef,
    Q,
    TextField,
    Value,
    When,
)
from django.db.models.functions import Concat, JSONObject
from django.urls import reverse
from django.utils.translation import gettext as _

from arches import __version__ as _arches_version_str
from arches.app.models import models

from packaging.version import Version

arches_version = Version(_arches_version_str)


class ArchesGetNodeDisplayValueV2(Func):
    function = "__arches_get_node_display_value_v2"
    output_field = TextField()
    arity = 3


class ArchesGetValueId(Func):
    function = "__arches_get_valueid"
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
        if (
            datatype == "concept-list" or datatype == "reference"
        ) and not is_user_rdm_admin:
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
    if arches_version >= Version("8.0"):
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
