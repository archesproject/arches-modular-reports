import re

from django.utils.translation import get_language, get_language_info

from arches.app.datatypes.datatypes import DataTypeFactory
from arches.app.models import models
from arches.app.models.tile import Tile

TEMPLATE_TOKEN = re.compile(r"<(.*?)>")


def name_node(graph_id):
    """The string node the graph's name descriptor starts with, if any."""
    descriptor_function = models.FunctionXGraph.objects.filter(
        graph_id=graph_id, function__functiontype="primarydescriptors"
    ).first()
    if descriptor_function is None:
        return None
    name_config = descriptor_function.config.get("descriptor_types", {}).get("name", {})
    tokens = TEMPLATE_TOKEN.findall(name_config.get("string_template", ""))
    if not tokens:
        return None
    string_nodes = models.Node.objects.filter(
        graph_id=graph_id, datatype="string", source_identifier__isnull=True
    )
    # The multi-card descriptor names nodes by alias; the default descriptor
    # names them by node name within its configured nodegroup.
    if node := string_nodes.filter(alias=tokens[0]).first():
        return node
    if nodegroup_id := name_config.get("nodegroup_id"):
        return string_nodes.filter(nodegroup_id=nodegroup_id, name=tokens[0]).first()
    return None


def name_value(resource):
    """The resource's name without the rest of its descriptor template."""
    node = name_node(resource.graph_id)
    if node is not None:
        # Descriptors read the first tile of the nodegroup, as here.
        tile = (
            models.TileModel.objects.filter(
                resourceinstance_id=resource.pk, nodegroup_id=node.nodegroup_id
            )
            .order_by("sortorder", "tileid")
            .first()
        )
        if tile is not None:
            value = (
                DataTypeFactory()
                .get_instance(node.datatype)
                .get_display_value(tile, node)
            )
            if value:
                return str(value)
    return str(resource.name or "")


def rename_copy(copied_resource, name):
    """Write `name` into the copy's name tile in the current language,
    leaving its other names and languages as copied."""
    node = name_node(copied_resource.graph_id)
    if node is None:
        return
    name_tiles = [
        tile
        for tile in all_tiles(copied_resource.tiles)
        if tile.nodegroup_id == node.nodegroup_id
    ]
    if name_tiles:
        name_tile = min(name_tiles, key=lambda tile: tile.sortorder or 0)
    elif node.nodegroup.parentnodegroup_id is None:
        name_tile = Tile.get_blank_tile_from_nodegroup_id(
            node.nodegroup_id, resourceid=copied_resource.pk
        )
        copied_resource.tiles.append(name_tile)
    else:
        return
    language = get_language()
    localized_value = dict(name_tile.data.get(str(node.pk)) or {})
    localized_value[language] = {
        "value": name,
        "direction": "rtl" if get_language_info(language)["bidi"] else "ltr",
    }
    name_tile.data[str(node.pk)] = localized_value


def all_tiles(tiles):
    for tile in tiles:
        yield tile
        yield from all_tiles(tile.tiles)
