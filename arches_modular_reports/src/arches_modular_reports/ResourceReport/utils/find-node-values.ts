import { isAliasedNodeData } from "@/arches_vue_components/generics/GenericCard/utils.ts";
import { nodegroupTiles } from "@/arches_modular_reports/ResourceReport/utils/tiles.ts";

import type {
    AliasedData,
    AliasedNodeData,
} from "@/arches_vue_components/types.ts";

export function findNodeValues(
    aliasedData: AliasedData,
    nodeAlias: string,
): AliasedNodeData[] {
    const foundValues: AliasedNodeData[] = [];
    for (const [alias, value] of Object.entries(aliasedData)) {
        if (isAliasedNodeData(value)) {
            if (alias === nodeAlias) {
                foundValues.push(value);
            }
        } else {
            for (const tile of nodegroupTiles(value)) {
                foundValues.push(
                    ...findNodeValues(tile.aliased_data, nodeAlias),
                );
            }
        }
    }
    return foundValues;
}
