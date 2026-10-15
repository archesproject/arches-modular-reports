import { isEqual } from "es-toolkit";

import { isAliasedNodeData } from "@/arches_vue_components/generics/GenericCard/utils.ts";
import { nodegroupTiles } from "@/arches_modular_reports/ResourceReport/utils/tiles.ts";

import type {
    AliasedData,
    AliasedNodeData,
    AliasedTileData,
} from "@/arches_vue_components/types.ts";
import type {
    AliasedResourceData,
    EditTileChange,
    ReorderTilesChange,
    ResourceChange,
} from "@/arches_modular_reports/ResourceReport/types.ts";

function reorderTiles(
    tiles: AliasedTileData[],
    orderedTileIds: string[] | undefined,
): AliasedTileData[] {
    if (orderedTileIds === undefined) {
        return tiles;
    }
    const positions = new Map(
        orderedTileIds.map((tileId, position) => [tileId, position]),
    );
    return tiles
        .map((tile) => {
            const position = positions.get(tile.tileid ?? "");
            if (position === undefined || position === tile.sortorder) {
                return tile;
            }
            return { ...tile, sortorder: position };
        })
        .sort(
            (firstTile, secondTile) =>
                firstTile.sortorder - secondTile.sortorder,
        );
}

function applyToTile(
    tile: AliasedTileData,
    changes: ResourceChange[],
    shouldRemoveDeletedTiles: boolean,
): AliasedTileData {
    const edit = changes.find(
        (change) => change.type === "edit" && change.tileId === tile.tileid,
    );
    let editedAliasedData = tile.aliased_data;
    if (edit?.type === "edit") {
        editedAliasedData = { ...tile.aliased_data, ...edit.aliasedData };
    }
    const nextAliasedData = applyToAliasedData(
        editedAliasedData,
        tile.tileid,
        changes,
        shouldRemoveDeletedTiles,
    );
    if (nextAliasedData === tile.aliased_data) {
        return tile;
    }
    return { ...tile, aliased_data: nextAliasedData };
}

function applyToAliasedData(
    aliasedData: AliasedData,
    parentTileId: string | null,
    changes: ResourceChange[],
    shouldRemoveDeletedTiles: boolean,
): AliasedData {
    const addedTilesByNodegroupAlias = new Map<string, AliasedTileData[]>();
    const orderedTileIdsByNodegroupAlias = new Map<string, string[]>();
    for (const change of changes) {
        if (change.type === "add" && change.parentTileId === parentTileId) {
            addedTilesByNodegroupAlias.set(change.nodegroupAlias, [
                ...(addedTilesByNodegroupAlias.get(change.nodegroupAlias) ??
                    []),
                change.tile,
            ]);
        }
        if (change.type === "reorder" && change.parentTileId === parentTileId) {
            orderedTileIdsByNodegroupAlias.set(
                change.nodegroupAlias,
                change.tileIds,
            );
        }
    }
    const deletedTileIds = new Set(
        changes.flatMap((change) =>
            change.type === "delete" ? [change.tileId] : [],
        ),
    );

    let updatedAliasedData: AliasedData | null = null;
    const nodegroupAliases = new Set([
        ...Object.keys(aliasedData),
        ...addedTilesByNodegroupAlias.keys(),
    ]);
    for (const nodegroupAlias of nodegroupAliases) {
        const value = aliasedData[nodegroupAlias];
        if (isAliasedNodeData(value)) {
            continue;
        }
        const tiles = nodegroupTiles(value);
        let keptTiles = tiles;
        if (shouldRemoveDeletedTiles) {
            keptTiles = tiles.filter(
                (tile) => !deletedTileIds.has(tile.tileid ?? ""),
            );
        }
        const nextTiles = reorderTiles(
            [
                ...keptTiles,
                ...(addedTilesByNodegroupAlias.get(nodegroupAlias) ?? []),
            ].map((tile) =>
                applyToTile(tile, changes, shouldRemoveDeletedTiles),
            ),
            orderedTileIdsByNodegroupAlias.get(nodegroupAlias),
        );
        if (
            nextTiles.length === tiles.length &&
            nextTiles.every((tile, index) => tile === tiles[index])
        ) {
            continue;
        }
        updatedAliasedData ??= { ...aliasedData };
        if (Array.isArray(value) || value === undefined) {
            updatedAliasedData[nodegroupAlias] = nextTiles;
        } else {
            updatedAliasedData[nodegroupAlias] = nextTiles[0] ?? null;
        }
    }
    return updatedAliasedData ?? aliasedData;
}

export function applyResourceChanges(
    resource: AliasedResourceData,
    changes: ResourceChange[],
): AliasedResourceData {
    const nextAliasedData = applyToAliasedData(
        resource.aliased_data,
        null,
        changes,
        false,
    );
    if (nextAliasedData === resource.aliased_data) {
        return resource;
    }
    return { ...resource, aliased_data: nextAliasedData };
}

export function parentTileIdsByTileId(
    aliasedData: AliasedData,
    parentTileId: string | null = null,
    parentTileIds: Map<string, string | null> = new Map(),
): Map<string, string | null> {
    for (const value of Object.values(aliasedData)) {
        for (const tile of nodegroupTiles(value)) {
            if (tile.tileid) {
                parentTileIds.set(tile.tileid, parentTileId);
                parentTileIdsByTileId(
                    tile.aliased_data,
                    tile.tileid,
                    parentTileIds,
                );
            }
        }
    }
    return parentTileIds;
}

export function findTile(
    aliasedData: AliasedData,
    tileId: string,
): AliasedTileData | null {
    for (const value of Object.values(aliasedData)) {
        for (const tile of nodegroupTiles(value)) {
            if (tile.tileid === tileId) {
                return tile;
            }
            const nestedTile = findTile(tile.aliased_data, tileId);
            if (nestedTile) {
                return nestedTile;
            }
        }
    }
    return null;
}

export function ownNodeData(
    aliasedData: AliasedData,
): Record<string, AliasedNodeData> {
    const nodeDataByAlias: Record<string, AliasedNodeData> = {};
    for (const [nodeAlias, value] of Object.entries(aliasedData)) {
        if (isAliasedNodeData(value)) {
            nodeDataByAlias[nodeAlias] = value;
        }
    }
    return nodeDataByAlias;
}

export function siblingTiles(
    aliasedData: AliasedData,
    nodegroupAlias: string,
    parentTileId: string | null,
): AliasedTileData[] {
    if (parentTileId === null) {
        return nodegroupTiles(aliasedData[nodegroupAlias]);
    }
    return nodegroupTiles(
        findTile(aliasedData, parentTileId)?.aliased_data[nodegroupAlias],
    );
}

function withChangedNodesOnly(
    editChange: EditTileChange,
    resource: AliasedResourceData,
): EditTileChange | null {
    const serverTile = findTile(resource.aliased_data, editChange.tileId);
    if (serverTile === null) {
        return editChange;
    }
    const changedNodeEntries = Object.entries(editChange.aliasedData).filter(
        ([nodeAlias, nodeData]) => {
            const serverNodeData = serverTile.aliased_data[nodeAlias];
            return (
                !isAliasedNodeData(serverNodeData) ||
                !isEqual(nodeData.node_value, serverNodeData.node_value)
            );
        },
    );
    if (changedNodeEntries.length === 0) {
        return null;
    }
    if (
        changedNodeEntries.length === Object.keys(editChange.aliasedData).length
    ) {
        return editChange;
    }
    return {
        ...editChange,
        aliasedData: Object.fromEntries(changedNodeEntries),
    };
}

function keepsCurrentOrder(
    reorderChange: ReorderTilesChange,
    resource: AliasedResourceData,
    changes: ResourceChange[],
): boolean {
    const workingResource = applyResourceChanges(
        resource,
        changes.filter((change) => change !== reorderChange),
    );
    const currentTileIds = siblingTiles(
        workingResource.aliased_data,
        reorderChange.nodegroupAlias,
        reorderChange.parentTileId,
    ).map((tile) => tile.tileid);
    return isEqual(currentTileIds, reorderChange.tileIds);
}

export function rebaseChanges(
    changes: ResourceChange[],
    resource: AliasedResourceData,
): ResourceChange[] {
    const existingTileIds = new Set(
        parentTileIdsByTileId(resource.aliased_data).keys(),
    );
    const rebasedChanges: ResourceChange[] = [];
    for (const change of changes) {
        let rebasedChange: ResourceChange | null = change;
        if (change.type === "add" && existingTileIds.has(change.tile.tileid)) {
            rebasedChange = withChangedNodesOnly(
                {
                    id: change.id,
                    type: "edit",
                    nodegroupAlias: change.nodegroupAlias,
                    tileId: change.tile.tileid,
                    aliasedData: ownNodeData(change.tile.aliased_data),
                },
                resource,
            );
        } else if (change.type === "edit") {
            rebasedChange = withChangedNodesOnly(change, resource);
        }
        if (rebasedChange !== null) {
            rebasedChanges.push(rebasedChange);
        }
    }
    return rebasedChanges.filter(
        (change) =>
            change.type !== "reorder" ||
            !keepsCurrentOrder(change, resource, rebasedChanges),
    );
}

export function replayResourceChanges(
    resource: AliasedResourceData,
    changes: ResourceChange[],
): { resource: AliasedResourceData; conflictingChanges: ResourceChange[] } {
    const existingTileIds = new Set(
        parentTileIdsByTileId(resource.aliased_data).keys(),
    );
    const addedTileIds = new Set(
        changes.flatMap((change) =>
            change.type === "add" ? [change.tile.tileid] : [],
        ),
    );

    function isPresent(tileId: string | null): boolean {
        return (
            tileId === null ||
            existingTileIds.has(tileId) ||
            addedTileIds.has(tileId)
        );
    }

    const conflictingChanges = changes.filter((change) => {
        if (change.type === "add" || change.type === "reorder") {
            return !isPresent(change.parentTileId);
        }
        return !existingTileIds.has(change.tileId);
    });

    return {
        resource: {
            ...resource,
            aliased_data: applyToAliasedData(
                resource.aliased_data,
                null,
                rebaseChanges(changes, resource),
                true,
            ),
        },
        conflictingChanges,
    };
}
