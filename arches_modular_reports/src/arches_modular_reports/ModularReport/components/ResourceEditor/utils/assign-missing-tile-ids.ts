import { isAliasedNodeData } from "@/arches_vue_components/generics/GenericCard/utils.ts";

import type { AliasedData } from "@/arches_modular_reports/ModularReport/types.ts";

export function assignMissingTileIds(aliasedData: AliasedData): void {
    for (const value of Object.values(aliasedData)) {
        const tiles = Array.isArray(value) ? value : [value];

        for (const tile of tiles) {
            if (tile === null) {
                continue;
            }
            if (isAliasedNodeData(tile)) {
                continue;
            }

            if (!tile.tileid) {
                tile.tileid = crypto.randomUUID();
            }

            assignMissingTileIds(tile.aliased_data);
        }
    }
}
