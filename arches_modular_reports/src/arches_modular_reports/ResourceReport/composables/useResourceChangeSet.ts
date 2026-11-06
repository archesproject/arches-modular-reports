import { computed, ref, shallowRef, watchEffect } from "vue";

import { fetchTileData } from "@/arches_vue_components/generics/GenericCard/api.ts";
import {
    extractAliasedNodeDataEntries,
    isAliasedNodeData,
} from "@/arches_vue_components/generics/GenericCard/utils.ts";
import {
    fetchResource,
    ResourceConflictError,
    saveResourceChanges,
} from "@/arches_modular_reports/ResourceReport/api.ts";
import {
    applyResourceChanges,
    findTile,
    loadedNodeValues,
    parentTileIdsByTileId,
    rebaseChanges,
    siblingTiles,
    withLoadedOriginals,
} from "@/arches_modular_reports/ResourceReport/utils/resource-change-set.ts";

import type {
    AliasedData,
    AliasedTileData,
} from "@/arches_vue_components/types.ts";
import type {
    AddTileChange,
    AliasedResourceData,
    ChangeConflict,
    EditTileChange,
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
    const conflicts = ref<ChangeConflict[]>([]);
    const hasConflicted = ref(false);
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

    const conflictsResolved = computed(
        () =>
            hasConflicted.value &&
            conflicts.value.length === 0 &&
            pendingChanges.value.length > 0,
    );

    function setPendingChanges(changes: ResourceChange[]): void {
        if (resource.value === null) {
            pendingChanges.value = changes;
        } else {
            pendingChanges.value = rebaseChanges(changes, resource.value);
        }
        pruneConflicts();
    }

    // Drops conflicts whose change is gone, and parent_deleted conflicts whose
    // parent is back (e.g. restored by the user).
    function pruneConflicts(): void {
        if (conflicts.value.length === 0) {
            return;
        }
        const presentTileIds = new Set([
            ...parentTileIdsByTileId(resource.value?.aliased_data ?? {}).keys(),
            ...pendingChanges.value.flatMap((change) =>
                change.type === "add" ? [change.tile.tileid] : [],
            ),
        ]);
        const remainingConflicts = conflicts.value.filter((conflict) => {
            const change = pendingChanges.value.find(
                (pendingChange) => pendingChange.id === conflict.changeId,
            );
            if (change === undefined) {
                return false;
            }
            if (
                conflict.reason === "parent_deleted" &&
                (change.type === "add" || change.type === "reorder")
            ) {
                return (
                    change.parentTileId !== null &&
                    !presentTileIds.has(change.parentTileId)
                );
            }
            return true;
        });
        if (remainingConflicts.length !== conflicts.value.length) {
            conflicts.value = remainingConflicts;
        }
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
        const nodeAliases = Object.keys(nodeDataByAlias);
        const loadedValues = loadedNodeValues(
            resource.value === null
                ? null
                : findTile(resource.value.aliased_data, tileId),
            nodeAliases,
        );

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
                    original: { ...loadedValues, ...change.original },
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
            original: loadedValues,
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
        conflicts.value = [];
        hasConflicted.value = false;
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
        conflicts.value = [];
        hasConflicted.value = false;
        const sentChanges = pendingChanges.value;
        try {
            const savedResource = await saveResourceChanges(
                graphSlug,
                resourceInstanceId,
                sentChanges,
            );
            resource.value = savedResource;
            setPendingChanges(
                pendingChanges.value
                    .filter((change) => !sentChanges.includes(change))
                    .map((change) =>
                        withLoadedOriginals(change, savedResource),
                    ),
            );
            return true;
        } catch (error) {
            if (
                error instanceof ResourceConflictError &&
                error.conflicts.length > 0
            ) {
                showConflicts(error);
            } else {
                saveError.value = error as Error;
            }
            return false;
        } finally {
            isSaving.value = false;
        }
    }

    function showConflicts(error: ResourceConflictError): void {
        const previousWorkingResource = workingResource.value ?? error.resource;
        conflicts.value = error.conflicts.map((conflict) => {
            const snapshot =
                conflict.reason === "deleted" && conflict.tileId
                    ? findTile(
                          previousWorkingResource.aliased_data,
                          conflict.tileId,
                      )
                    : null;
            if (snapshot?.tileid) {
                return {
                    ...conflict,
                    tileSnapshot: snapshot as ChangeConflict["tileSnapshot"],
                };
            }
            return conflict;
        });
        hasConflicted.value = true;
        resource.value = error.resource;
        setPendingChanges(pendingChanges.value);
    }

    function insertAdd(
        changes: ResourceChange[],
        addChange: AddTileChange,
    ): ResourceChange[] {
        const parentAddIndex = changes.findIndex(
            (change) =>
                change.type === "add" &&
                change.tile.tileid === addChange.parentTileId,
        );
        return [
            ...changes.slice(0, parentAddIndex + 1),
            addChange,
            ...changes.slice(parentAddIndex + 1),
        ];
    }

    function restoreDeletedTile(
        change: EditTileChange,
        conflict: ChangeConflict,
    ): boolean {
        const snapshot = conflict.tileSnapshot;
        if (snapshot === undefined) {
            return false;
        }
        const restoredAdd: AddTileChange = {
            id: change.id,
            type: "add",
            nodegroupAlias: change.nodegroupAlias,
            parentTileId: snapshot.parenttile,
            tile: {
                ...snapshot,
                aliased_data: withoutChildTiles(snapshot.aliased_data),
            },
        };
        setPendingChanges(
            insertAdd(
                pendingChanges.value.filter(
                    (pendingChange) => pendingChange.id !== change.id,
                ),
                restoredAdd,
            ),
        );
        return true;
    }

    function replaceTakenSlot(addChange: AddTileChange): boolean {
        if (resource.value === null) {
            return false;
        }
        const occupant = siblingTiles(
            resource.value.aliased_data,
            addChange.nodegroupAlias,
            addChange.parentTileId,
        )[0];
        if (!occupant?.tileid) {
            return false;
        }
        const aliasedData = extractAliasedNodeDataEntries(
            addChange.tile.aliased_data,
        );
        const editChange: EditTileChange = {
            id: addChange.id,
            type: "edit",
            nodegroupAlias: addChange.nodegroupAlias,
            tileId: occupant.tileid,
            aliasedData,
            original: loadedNodeValues(occupant, Object.keys(aliasedData)),
        };
        const addedTileId = addChange.tile.tileid;
        setPendingChanges(
            pendingChanges.value.map((change) => {
                if (change.id === addChange.id) {
                    return editChange;
                }
                if (
                    change.type === "add" &&
                    change.parentTileId === addedTileId
                ) {
                    return {
                        ...change,
                        parentTileId: occupant.tileid,
                        tile: { ...change.tile, parenttile: occupant.tileid },
                    };
                }
                if (
                    change.type === "reorder" &&
                    change.parentTileId === addedTileId
                ) {
                    return { ...change, parentTileId: occupant.tileid };
                }
                return change;
            }),
        );
        return true;
    }

    function keepMine(changeId: string): void {
        const conflict = conflicts.value.find(
            (candidate) => candidate.changeId === changeId,
        );
        const change = pendingChanges.value.find(
            (candidate) => candidate.id === changeId,
        );
        if (conflict === undefined || change === undefined) {
            return;
        }
        if (conflict.reason === "modified" && change.type === "edit") {
            const currentValues = Object.fromEntries(
                Object.entries(conflict.nodes ?? {}).map(
                    ([nodeAlias, node]) => [nodeAlias, node.current],
                ),
            );
            setPendingChanges(
                pendingChanges.value.map((pendingChange) =>
                    pendingChange.id === changeId &&
                    pendingChange.type === "edit"
                        ? {
                              ...pendingChange,
                              original: {
                                  ...pendingChange.original,
                                  ...currentValues,
                              },
                          }
                        : pendingChange,
                ),
            );
            conflicts.value = conflicts.value.filter(
                (candidate) => candidate.changeId !== changeId,
            );
        } else if (conflict.reason === "deleted" && change.type === "edit") {
            if (restoreDeletedTile(change, conflict)) {
                conflicts.value = conflicts.value.filter(
                    (candidate) => candidate.changeId !== changeId,
                );
            }
        } else if (conflict.reason === "slot_taken" && change.type === "add") {
            if (replaceTakenSlot(change)) {
                conflicts.value = conflicts.value.filter(
                    (candidate) => candidate.changeId !== changeId,
                );
            }
        }
        pruneConflicts();
    }

    function useTheirs(changeId: string): void {
        const conflict = conflicts.value.find(
            (candidate) => candidate.changeId === changeId,
        );
        const change = pendingChanges.value.find(
            (candidate) => candidate.id === changeId,
        );
        if (
            conflict?.reason !== "modified" ||
            change?.type !== "edit" ||
            conflict.nodes === undefined
        ) {
            discardChange(changeId);
            return;
        }
        const conflictingAliases = new Set(Object.keys(conflict.nodes));
        const keepAliases = <T>(record: Record<string, T>) =>
            Object.fromEntries(
                Object.entries(record).filter(
                    ([nodeAlias]) => !conflictingAliases.has(nodeAlias),
                ),
            ) as Record<string, T>;
        const aliasedData = keepAliases(change.aliasedData);
        if (Object.keys(aliasedData).length === 0) {
            discardChange(changeId);
            return;
        }
        conflicts.value = conflicts.value.filter(
            (candidate) => candidate.changeId !== changeId,
        );
        setPendingChanges(
            pendingChanges.value.map((pendingChange) =>
                pendingChange.id === changeId && pendingChange.type === "edit"
                    ? {
                          ...pendingChange,
                          aliasedData,
                          original: keepAliases(pendingChange.original),
                      }
                    : pendingChange,
            ),
        );
    }

    function keepAllMine(): void {
        for (const conflict of [...conflicts.value]) {
            keepMine(conflict.changeId);
        }
    }

    function discardAllConflicting(): void {
        const conflictingIds = new Set(
            conflicts.value.map((conflict) => conflict.changeId),
        );
        for (const changeId of conflictingIds) {
            if (pendingChanges.value.some((change) => change.id === changeId)) {
                discardChange(changeId);
            }
        }
        conflicts.value = [];
    }

    return {
        workingResource,
        pendingChanges,
        conflicts,
        conflictsResolved,
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
        keepMine,
        useTheirs,
        keepAllMine,
        discardAllConflicting,
        changeTypeForTile,
        isPendingDelete,
        save,
    };
}
