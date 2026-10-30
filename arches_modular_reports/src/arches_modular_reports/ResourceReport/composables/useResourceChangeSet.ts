import { computed, ref, shallowRef, watchEffect } from "vue";

import { fetchTileData } from "@/arches_vue_components/generics/GenericCard/api.ts";
import {
    extractAliasedNodeDataEntries,
    isAliasedNodeData,
} from "@/arches_vue_components/generics/GenericCard/utils.ts";
import {
    fetchResource,
    updateResource,
} from "@/arches_modular_reports/ResourceReport/api.ts";
import {
    applyResourceChanges,
    parentTileIdsByTileId,
    rebaseChanges,
    replayResourceChanges,
    siblingTiles,
} from "@/arches_modular_reports/ResourceReport/utils/resource-change-set.ts";

import type {
    AliasedData,
    AliasedTileData,
} from "@/arches_vue_components/types.ts";
import type {
    AliasedResourceData,
    ResourceChange,
    ResourceChangeSet,
    TileChangeType,
} from "@/arches_modular_reports/ResourceReport/types.ts";

function withoutChildTiles(aliasedData: AliasedData): AliasedData {
    const ownAliasedData: AliasedData = {};
    for (const [alias, value] of Object.entries(aliasedData)) {
        if (isAliasedNodeData(value)) {
            ownAliasedData[alias] = value;
        } else if (Array.isArray(value)) {
            ownAliasedData[alias] = [];
        } else {
            ownAliasedData[alias] = null;
        }
    }
    return ownAliasedData;
}

export function useResourceChangeSet(
    graphSlug: string,
    resourceInstanceId: string,
): ResourceChangeSet {
    const resource = shallowRef<AliasedResourceData | null>(null);
    const pendingChanges = shallowRef<ResourceChange[]>([]);
    const conflictingChangeIds = ref<string[]>([]);
    const fetchError = ref<Error | null>(null);
    const isSaving = ref(false);
    const saveError = ref<Error | null>(null);
    const addError = ref<Error | null>(null);
    const isAdding = ref(false);

    const workingResource = computed(() => {
        if (resource.value === null) {
            return null;
        }
        return applyResourceChanges(resource.value, pendingChanges.value);
    });

    const isBusy = computed(() => isSaving.value || isAdding.value);

    const parentTileIds = computed(() => {
        if (workingResource.value === null) {
            return new Map<string, string | null>();
        }
        return parentTileIdsByTileId(workingResource.value.aliased_data);
    });

    watchEffect(async () => {
        fetchError.value = null;
        try {
            resource.value = await fetchResource(graphSlug, resourceInstanceId);
        } catch (error) {
            fetchError.value = error as Error;
        }
    });

    function isWithin(tileId: string | null, ancestorTileId: string): boolean {
        let currentTileId = tileId;
        while (currentTileId !== null) {
            if (currentTileId === ancestorTileId) {
                return true;
            }
            currentTileId = parentTileIds.value.get(currentTileId) ?? null;
        }
        return false;
    }

    function setPendingChanges(changes: ResourceChange[]): void {
        if (resource.value === null) {
            pendingChanges.value = changes;
            return;
        }
        pendingChanges.value = rebaseChanges(changes, resource.value);
    }

    function replaceChange(updatedChange: ResourceChange): void {
        setPendingChanges(
            pendingChanges.value.map((change) =>
                change.id === updatedChange.id ? updatedChange : change,
            ),
        );
    }

    function appendChange(change: ResourceChange): void {
        setPendingChanges([...pendingChanges.value, change]);
    }

    async function addTile(
        nodegroupAlias: string,
        parentTileId: string | null,
    ): Promise<string | null> {
        if (isAdding.value) {
            return null;
        }
        isAdding.value = true;
        addError.value = null;
        let blankTile: AliasedTileData;
        try {
            blankTile = await fetchTileData(graphSlug, nodegroupAlias);
        } catch (error) {
            addError.value = error as Error;
            return null;
        } finally {
            isAdding.value = false;
        }
        const newTileId = crypto.randomUUID();
        appendChange({
            id: crypto.randomUUID(),
            type: "add",
            nodegroupAlias,
            parentTileId,
            tile: {
                ...blankTile,
                aliased_data: withoutChildTiles(blankTile.aliased_data),
                tileid: newTileId,
                parenttile: parentTileId,
                resourceinstance: resourceInstanceId,
                sortorder: siblingTiles(
                    workingResource.value?.aliased_data ?? {},
                    nodegroupAlias,
                    parentTileId,
                ).reduce(
                    (nextSortorder, siblingTile) =>
                        Math.max(nextSortorder, siblingTile.sortorder + 1),
                    0,
                ),
            },
        });
        return newTileId;
    }

    function editTile(
        nodegroupAlias: string,
        tileId: string,
        aliasedData: AliasedData,
    ): void {
        const nodeDataByAlias = extractAliasedNodeDataEntries(aliasedData);

        for (const change of pendingChanges.value) {
            if (change.type === "add" && change.tile.tileid === tileId) {
                replaceChange({
                    ...change,
                    tile: {
                        ...change.tile,
                        aliased_data: {
                            ...change.tile.aliased_data,
                            ...nodeDataByAlias,
                        },
                    },
                });
                return;
            }
            if (change.type === "edit" && change.tileId === tileId) {
                replaceChange({
                    ...change,
                    aliasedData: { ...change.aliasedData, ...nodeDataByAlias },
                });
                return;
            }
        }
        appendChange({
            id: crypto.randomUUID(),
            type: "edit",
            nodegroupAlias,
            tileId,
            aliasedData: nodeDataByAlias,
        });
    }

    function deleteTile(nodegroupAlias: string, tileId: string): void {
        const pendingAdd = pendingChanges.value.find(
            (change) => change.type === "add" && change.tile.tileid === tileId,
        );
        if (pendingAdd) {
            discardChange(pendingAdd.id);
            return;
        }
        if (changeTypeForTile(tileId) !== "delete") {
            appendChange({
                id: crypto.randomUUID(),
                type: "delete",
                nodegroupAlias,
                tileId,
            });
        }
    }

    function undoDelete(tileId: string): void {
        setPendingChanges(
            pendingChanges.value.filter(
                (change) =>
                    !(change.type === "delete" && change.tileId === tileId),
            ),
        );
    }

    function reorderTiles(
        nodegroupAlias: string,
        parentTileId: string | null,
        orderedTileIds: string[],
    ): void {
        const existingReorder = pendingChanges.value.find(
            (change) =>
                change.type === "reorder" &&
                change.nodegroupAlias === nodegroupAlias &&
                change.parentTileId === parentTileId,
        );
        if (existingReorder?.type === "reorder") {
            replaceChange({ ...existingReorder, tileIds: orderedTileIds });
            return;
        }
        appendChange({
            id: crypto.randomUUID(),
            type: "reorder",
            nodegroupAlias,
            parentTileId,
            tileIds: orderedTileIds,
        });
    }

    function discardChange(changeId: string): void {
        const discardedChange = pendingChanges.value.find(
            (change) => change.id === changeId,
        );
        if (discardedChange?.type !== "add") {
            setPendingChanges(
                pendingChanges.value.filter((change) => change.id !== changeId),
            );
            return;
        }
        const addedTileId = discardedChange.tile.tileid;
        setPendingChanges(
            pendingChanges.value.filter((change) => {
                if (change.id === changeId) {
                    return false;
                }
                if (change.type === "add" || change.type === "reorder") {
                    return !isWithin(change.parentTileId, addedTileId);
                }
                return !isWithin(change.tileId, addedTileId);
            }),
        );
    }

    function discardAll(): void {
        pendingChanges.value = [];
        conflictingChangeIds.value = [];
    }

    function changeTypeForTile(tileId: string): TileChangeType | null {
        let changeType: TileChangeType | null = null;
        for (const change of pendingChanges.value) {
            if (change.type === "delete" && change.tileId === tileId) {
                return "delete";
            }
            if (change.type === "add" && change.tile.tileid === tileId) {
                changeType = "add";
            }
            if (change.type === "edit" && change.tileId === tileId) {
                changeType ??= "edit";
            }
        }
        return changeType;
    }

    function isPendingDelete(tileId: string): boolean {
        return pendingChanges.value.some(
            (change) =>
                change.type === "delete" && isWithin(tileId, change.tileId),
        );
    }

    async function save(): Promise<boolean> {
        isSaving.value = true;
        saveError.value = null;
        conflictingChangeIds.value = [];
        const sentChanges = pendingChanges.value;
        try {
            const freshResource = await fetchResource(
                graphSlug,
                resourceInstanceId,
            );
            const { resource: replayedResource, conflictingChanges } =
                replayResourceChanges(
                    freshResource,
                    sentChanges,
                    resource.value ?? freshResource,
                );
            if (conflictingChanges.length > 0) {
                resource.value = freshResource;
                setPendingChanges(pendingChanges.value);
                conflictingChangeIds.value = conflictingChanges.map(
                    (change) => change.id,
                );
                return false;
            }
            resource.value = await updateResource(graphSlug, replayedResource);
            setPendingChanges(
                pendingChanges.value.filter(
                    (change) => !sentChanges.includes(change),
                ),
            );
            return true;
        } catch (error) {
            saveError.value = error as Error;
            return false;
        } finally {
            isSaving.value = false;
        }
    }

    return {
        workingResource,
        pendingChanges,
        conflictingChangeIds,
        fetchError,
        isSaving,
        isBusy,
        saveError,
        addError,
        addTile,
        editTile,
        deleteTile,
        undoDelete,
        reorderTiles,
        discardChange,
        discardAll,
        changeTypeForTile,
        isPendingDelete,
        save,
    };
}
