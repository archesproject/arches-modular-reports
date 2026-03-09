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
    data: Record<string, unknown>,
    nodegroupAlias: string,
    tileId: string | null | undefined,
    currentPath: Array<string | number> = [],
): Array<string | number> | null {
    const aliasedData = data["aliased_data"] as
        | Record<string, unknown>
        | undefined;
    if (!aliasedData) return null;

    const aliasedDataPath = [...currentPath, "aliased_data"];

    // Check whether the target nodegroup alias exists at this level.
    if (nodegroupAlias in aliasedData) {
        const nodegroupValue = aliasedData[nodegroupAlias];
        const nodegroupPath = [...aliasedDataPath, nodegroupAlias];

        if (Array.isArray(nodegroupValue)) {
            if (tileId) {
                const tileIndex = (
                    nodegroupValue as Array<{ tileid?: string | null }>
                ).findIndex((tile) => tile.tileid === tileId);
                if (tileIndex >= 0) {
                    return [...nodegroupPath, tileIndex];
                }
            } else {
                return nodegroupPath;
            }
        } else {
            // cardinality-1: value may be a tile object or null (empty slot).
            // Either way the path to this slot is what the caller needs.
            return nodegroupPath;
        }
    }

    // Recurse into any nested tiles at this level.
    for (const [key, value] of Object.entries(aliasedData)) {
        if (Array.isArray(value)) {
            for (let i = 0; i < value.length; i++) {
                const tile = value[i];
                if (
                    tile !== null &&
                    typeof tile === "object" &&
                    "aliased_data" in tile
                ) {
                    const result = findTilePathInResourceData(
                        tile as Record<string, unknown>,
                        nodegroupAlias,
                        tileId,
                        [...aliasedDataPath, key, i],
                    );
                    if (result) return result;
                }
            }
        } else if (
            value !== null &&
            typeof value === "object" &&
            "aliased_data" in value
        ) {
            const result = findTilePathInResourceData(
                value as Record<string, unknown>,
                nodegroupAlias,
                tileId,
                [...aliasedDataPath, key],
            );
            if (result) return result;
        }
    }

    return null;
}
