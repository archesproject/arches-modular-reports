import type {
    AliasedData,
    AliasedNodeData,
    AliasedTileData,
} from "@/arches_vue_components/types.ts";

function isTileData(
    value: AliasedNodeData | AliasedTileData,
): value is AliasedTileData {
    return "aliased_data" in value;
}

export function findNodeValues(
    aliasedData: AliasedData,
    nodeAlias: string,
): AliasedNodeData[] {
    const foundValues: AliasedNodeData[] = [];

    function visit(currentAliasedData: AliasedData): void {
        for (const [alias, value] of Object.entries(currentAliasedData)) {
            if (value === null) {
                continue;
            }
            if (Array.isArray(value)) {
                for (const tile of value) {
                    visit(tile.aliased_data);
                }
                continue;
            }
            if (isTileData(value)) {
                visit(value.aliased_data);
                continue;
            }
            if (alias === nodeAlias) {
                foundValues.push(value);
            }
        }
    }

    visit(aliasedData);
    return foundValues;
}
