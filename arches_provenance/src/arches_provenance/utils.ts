type TileValue = any;
type Tile = { [key: string]: TileValue };

export function findNodeValue(
    labelBasedResource: { [key: string]: any },
    nodeAlias: string,
): TileValue {
    function searchSiblingNodes(tile: Tile): TileValue {
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
