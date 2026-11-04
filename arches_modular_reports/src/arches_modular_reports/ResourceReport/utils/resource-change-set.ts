import { isEqual } from "es-toolkit";

import {
    extractAliasedNodeDataEntries,
    isAliasedNodeData,
} from "@/arches_vue_components/generics/GenericCard/utils.ts";
import { nodegroupTiles } from "@/arches_modular_reports/ResourceReport/utils/tiles.ts";

import type {
    AliasedData,
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
        const nextTiles = reorderTiles(
            [
                ...tiles,
                ...(addedTilesByNodegroupAlias.get(nodegroupAlias) ?? []),
            ].map((tile) => applyToTile(tile, changes)),
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

export function loadedNodeValues(
    tile: AliasedTileData | null,
    nodeAliases: string[],
): Record<string, unknown> {
    const nodeValues: Record<string, unknown> = {};
    for (const nodeAlias of nodeAliases) {
        const nodeData = tile?.aliased_data[nodeAlias];
        nodeValues[nodeAlias] = isAliasedNodeData(nodeData)
            ? nodeData.node_value
            : null;
    }
    return nodeValues;
}

// Re-anchors an edit's originals to a freshly loaded resource.
export function withLoadedOriginals(
    change: ResourceChange,
    resource: AliasedResourceData,
): ResourceChange {
    if (change.type !== "edit") {
        return change;
    }
    return {
        ...change,
        original: loadedNodeValues(
            findTile(resource.aliased_data, change.tileId),
            Object.keys(change.aliasedData),
        ),
    };
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
    const changedAliasedData = Object.fromEntries(changedNodeEntries);
    return {
        ...editChange,
        aliasedData: changedAliasedData,
        original: Object.fromEntries(
            Object.entries(editChange.original).filter(
                ([nodeAlias]) => nodeAlias in changedAliasedData,
            ),
        ),
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
            const aliasedData = extractAliasedNodeDataEntries(
                change.tile.aliased_data,
            );
            rebasedChange = withChangedNodesOnly(
                {
                    id: change.id,
                    type: "edit",
                    nodegroupAlias: change.nodegroupAlias,
                    tileId: change.tile.tileid,
                    aliasedData,
                    original: loadedNodeValues(
                        findTile(resource.aliased_data, change.tile.tileid),
                        Object.keys(aliasedData),
                    ),
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
