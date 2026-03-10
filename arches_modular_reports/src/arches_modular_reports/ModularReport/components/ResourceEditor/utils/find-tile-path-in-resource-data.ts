import type { TileData } from "@/arches_modular_reports/ModularReport/types.ts";

/**
 * Recursively searches resourceData for a tile belonging to a given
 * nodegroupAlias (and optionally matching a specific tileId) and returns
 * the full path to that tile.
 *
 * This is necessary because DataSection.initiateEdit only knows the
 * nodegroup alias and tile ID — not the full path — which means nested
 * tiles (whose alias does not appear at the root of aliased_data) cannot
 * be located by a simple top-level lookup.
 */
export function findTilePathInResourceData(
    data: Pick<TileData, "aliased_data">,
    nodegroupAlias: string,
    tileId: string | null | undefined,
    currentPath: Array<string | number> = [],
): Array<string | number> | null {
    for (const [alias, value] of Object.entries(data.aliased_data)) {
        const aliasPath = [...currentPath, "aliased_data", alias];

        if (alias === nodegroupAlias) {
            if (!Array.isArray(value) || !tileId) {
                return aliasPath;
            }

            const matchIndex = value.findIndex(
                (tile) => tile.tileid === tileId,
            );
            if (matchIndex >= 0) {
                return [...aliasPath, matchIndex];
            }
        }

        let childNodes: [
            Pick<TileData, "aliased_data">,
            Array<string | number>,
        ][];
        if (Array.isArray(value)) {
            childNodes = value.map((tile, index) => [
                tile,
                [...aliasPath, index],
            ]);
        } else {
            childNodes = [[value as Pick<TileData, "aliased_data">, aliasPath]];
        }

        const found = childNodes
            .filter(([tile]) => tile?.aliased_data != null)
            .reduce<Array<string | number> | null>(function (
                result,
                [tile, tilePath],
            ) {
                return (
                    result ??
                    findTilePathInResourceData(
                        tile,
                        nodegroupAlias,
                        tileId,
                        tilePath,
                    )
                );
            }, null);

        if (found) {
            return found;
        }
    }

    return null;
}
