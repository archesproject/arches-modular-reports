import re

from arches.app.models import models
from arches.app.models.tile import Tile

TEMPLATE_TOKEN = re.compile(r"<(.*?)>")


def name_node(graph_id):
    descriptor_function = models.FunctionXGraph.objects.filter(
        graph_id=graph_id, function__functiontype="primarydescriptors"
    ).first()
    if descriptor_function is None:
        return None
    name_config = descriptor_function.config.get("descriptor_types", {}).get("name", {})
    tokens = TEMPLATE_TOKEN.findall(name_config.get("string_template", ""))
    if not tokens:
        return None
    graph_nodes = models.Node.objects.filter(
        graph_id=graph_id, source_identifier__isnull=True
    )
    if node := graph_nodes.filter(alias=tokens[0]).first():
        return node
    if nodegroup_id := name_config.get("nodegroup_id"):
        return graph_nodes.filter(nodegroup_id=nodegroup_id, name=tokens[0]).first()
    return None


def renamable_name_node(resource):
    node = name_node(resource.graph_id)
    if node is None:
        return None
    if node.nodegroup.parentnodegroup_id is None:
        return node
    if models.TileModel.objects.filter(
        resourceinstance_id=resource.pk, nodegroup_id=node.nodegroup_id
    ).exists():
        return node
    return None


def rename_copy(copied_resource, node, name_value):
    name_tiles = [
        tile
        for tile in all_tiles(copied_resource.tiles)
        if tile.nodegroup_id == node.nodegroup_id
    ]
    if name_tiles:
        name_tile = min(name_tiles, key=lambda tile: tile.sortorder or 0)
    else:
        name_tile = Tile.get_blank_tile_from_nodegroup_id(
            node.nodegroup_id, resourceid=copied_resource.pk
        )
        copied_resource.tiles.append(name_tile)
    name_tile.data[str(node.pk)] = name_value


def all_tiles(tiles):
    for tile in tiles:
        yield tile
        yield from all_tiles(tile.tiles)
