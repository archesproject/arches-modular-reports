import type { Tile, TileValue } from "@/arches_provenance/EditableReport/types";

export function findNodeValue(
    labelBasedResource: { resource: Tile },
    nodeAlias: string,
): TileValue | undefined {
    function searchSiblingNodes(tile: Tile): TileValue | undefined {
        for (const [tileNodeAlias, tileData] of Object.entries(tile)) {
            if (tileNodeAlias === nodeAlias) {
                return tileData;
            }
            if (tileData instanceof Array) {
                for (const childTile of tileData) {
                    const searchResult = searchSiblingNodes(childTile);
                    if (searchResult) {
                        return searchResult;
                    }
                }
            }
        }
    }
    return searchSiblingNodes(labelBasedResource.resource);
}
