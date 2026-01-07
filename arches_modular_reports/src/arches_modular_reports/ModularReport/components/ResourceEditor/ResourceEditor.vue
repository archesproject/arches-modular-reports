<script setup lang="ts">
import {
    computed,
    inject,
    reactive,
    readonly,
    ref,
    shallowRef,
    watch,
    watchEffect,
} from "vue";

import { isEqual } from "es-toolkit";
import { useGettext } from "vue3-gettext";

import Button from "primevue/button";
import Message from "primevue/message";
import Skeleton from "primevue/skeleton";
import Splitter from "primevue/splitter";
import SplitterPanel from "primevue/splitterpanel";
import ConfirmDialog from "primevue/confirmdialog";
import { useConfirm } from "primevue/useconfirm";

import DataTree from "@/arches_modular_reports/ModularReport/components/ResourceEditor/components/DataTree/DataTree.vue";
import GenericCard from "@/arches_component_lab/generics/GenericCard/GenericCard.vue";

import {
    fetchModularReportBlankTile,
    fetchModularReportResource,
    updateModularReportResource,
} from "@/arches_modular_reports/ModularReport/api.ts";

import { generateWidgetDirtyStates } from "@/arches_modular_reports/ModularReport/components/ResourceEditor/utils/generate-widget-dirty-states.ts";
import { getValueFromPath } from "@/arches_modular_reports/ModularReport/components/ResourceEditor/utils/get-value-from-path.ts";
import { pruneResourceData } from "@/arches_modular_reports/ModularReport/components/ResourceEditor/utils/prune-resource-data.ts";

import { EDIT } from "@/arches_component_lab/widgets/constants.ts";

import type { Ref } from "vue";
import type {
    NodeData,
    NodegroupData,
    NodePresentationLookup,
    ResourceData,
    TileData,
} from "@/arches_modular_reports/ModularReport/types.ts";
import type { WidgetDirtyStates } from "@/arches_modular_reports/ModularReport/components/ResourceEditor/types.ts";
import type { AliasedTileData } from "@/arches_component_lab/types";

type SoftDeletePayload = {
    softDeleteKey: string;
    nodegroupValuePath: Array<string | number>;
    nextIsSoftDeleted: boolean;
};

const { $gettext } = useGettext();
const confirm = useConfirm();

const CARDINALITY_N = "n" as const;

const graphSlug = inject<string>("graphSlug")!;
const resourceInstanceId = inject<string>("resourceInstanceId")!;
const nodePresentationLookup = inject<Ref<NodePresentationLookup>>(
    "nodePresentationLookup",
)!;

const {
    createTileRequestId,
    createTileRequestedNodegroupAlias,
    createTileRequestedTilePath,
} = inject("createTile") as {
    createTileRequestId: Ref<number>;
    createTileRequestedNodegroupAlias: Ref<string | null>;
    createTileRequestedTilePath?: Ref<Array<string | number> | null>;
};

const { selectedNodegroupAlias } = inject("selectedNodegroupAlias") as {
    selectedNodegroupAlias: Ref<string | null>;
};

const { selectedNodeAlias, setSelectedNodeAlias } = inject(
    "selectedNodeAlias",
) as {
    selectedNodeAlias: Ref<string | null>;
    setSelectedNodeAlias: (nodeAlias: string | null) => void;
};

const { selectedTileId, setSelectedTileId } = inject("selectedTileId") as {
    selectedTileId: Ref<string | null | undefined>;
    setSelectedTileId: (tileId: string | null | undefined) => void;
};

const { selectedTilePath, setSelectedTilePath } = inject(
    "selectedTilePath",
) as {
    selectedTilePath: Ref<Array<string | number> | null>;
    setSelectedTilePath: (path: Array<string | number> | null) => void;
};

const emit = defineEmits(["save"]);

const isLoading = ref(true);
const apiError = ref<Error | null>(null);

const resourceData = reactive<ResourceData>({} as ResourceData);
const originalResourceData = shallowRef<Readonly<ResourceData>>(
    {} as ResourceData,
);
const widgetDirtyStates = reactive<WidgetDirtyStates>({} as WidgetDirtyStates);

const unsavedTileKeys = shallowRef<Set<string>>(new Set<string>());

const softDeletedTileKeys = shallowRef<Set<string>>(new Set<string>());
const softDeletedValuePaths = shallowRef<Map<string, Array<string | number>>>(
    new Map<string, Array<string | number>>(),
);

const selectedTileKey = computed<string>(() => {
    if (selectedTileId.value) {
        return selectedTileId.value;
    }
    return JSON.stringify(selectedTilePath.value ?? []);
});

const isSelectedTileSoftDeleted = computed<boolean>(() => {
    if (!selectedTileId.value && !selectedTilePath.value) {
        return false;
    }

    return softDeletedTileKeys.value.has(selectedTileKey.value);
});

function replaceReactiveRecord(
    targetRecord: Record<string, unknown>,
    nextRecord: Record<string, unknown>,
) {
    for (const existingKey of Object.keys(targetRecord)) {
        delete targetRecord[existingKey];
    }
    Object.assign(targetRecord, nextRecord);
}

function setValueAtPath(
    targetObject: Record<string, unknown>,
    pathSegments: Array<string | number>,
    valueToAssign: unknown,
) {
    if (pathSegments.length === 0) {
        return;
    }

    const lastSegment = pathSegments[pathSegments.length - 1];
    const parentPathSegments = pathSegments.slice(0, -1);

    const parentContainer = parentPathSegments.reduce<
        Record<string | number, unknown>
    >(
        (currentContainer, currentSegment) =>
            currentContainer[currentSegment] as Record<
                string | number,
                unknown
            >,
        targetObject as unknown as Record<string | number, unknown>,
    );

    parentContainer[lastSegment] = valueToAssign;
}

function isCardinalityNNodegroup(nodegroupAlias: string) {
    return (
        nodePresentationLookup.value?.[nodegroupAlias]?.nodegroup
            ?.cardinality === CARDINALITY_N
    );
}

function isTileData(value: unknown): value is TileData {
    return (
        typeof value === "object" && value !== null && "aliased_data" in value
    );
}

function buildDirtyStatesForNewTile(tileData: TileData): WidgetDirtyStates {
    const tileAliasedData = (tileData?.aliased_data ?? {}) as Record<
        string,
        unknown
    >;

    const dirtyAliasedData: Record<string, unknown> = {};

    for (const [childAlias, childValue] of Object.entries(tileAliasedData)) {
        if (Array.isArray(childValue)) {
            dirtyAliasedData[childAlias] = childValue.map((nestedTile) =>
                buildDirtyStatesForNewTile(nestedTile),
            );
            continue;
        }

        if (isTileData(childValue)) {
            dirtyAliasedData[childAlias] =
                buildDirtyStatesForNewTile(childValue);
            continue;
        }

        dirtyAliasedData[childAlias] = true;
    }

    return { aliased_data: dirtyAliasedData } as unknown as WidgetDirtyStates;
}

function insertAtNodegroupPath(options: {
    targetRoot: Record<string, unknown>;
    nodegroupValuePath: Array<string | number>;
    valueToInsert: unknown;
    isCardinalityN: boolean;
}) {
    const existingNodegroupValue = getValueFromPath(
        options.targetRoot,
        options.nodegroupValuePath,
    );

    if (Array.isArray(existingNodegroupValue)) {
        existingNodegroupValue.push(options.valueToInsert);

        return [
            ...options.nodegroupValuePath,
            existingNodegroupValue.length - 1,
        ];
    }

    if (existingNodegroupValue == null && options.isCardinalityN) {
        setValueAtPath(options.targetRoot, options.nodegroupValuePath, [
            options.valueToInsert,
        ]);
        return [...options.nodegroupValuePath, 0];
    }

    if (existingNodegroupValue == null) {
        setValueAtPath(
            options.targetRoot,
            options.nodegroupValuePath,
            options.valueToInsert,
        );
        return [...options.nodegroupValuePath];
    }

    return null;
}

function sortPathsForSafeRemoval(paths: Array<Array<string | number>>) {
    return [...paths].sort((firstPath, secondPath) => {
        if (firstPath.length !== secondPath.length) {
            return secondPath.length - firstPath.length;
        }

        const firstPathFinalSegment = firstPath[firstPath.length - 1];
        const secondPathFinalSegment = secondPath[secondPath.length - 1];

        if (
            typeof firstPathFinalSegment === "number" &&
            typeof secondPathFinalSegment === "number"
        ) {
            return secondPathFinalSegment - firstPathFinalSegment;
        }

        return 0;
    });
}

function removeValueAtPath(
    targetRoot: Record<string | number, unknown>,
    pathSegments: Array<string | number>,
) {
    const lastSegment = pathSegments[pathSegments.length - 1];
    if (lastSegment == null) {
        return;
    }

    let parentContainer: unknown = targetRoot;

    for (const currentSegment of pathSegments.slice(0, -1)) {
        parentContainer = (
            parentContainer as Record<string | number, unknown> | undefined
        )?.[currentSegment];

        if (parentContainer == null) {
            return;
        }
    }

    if (Array.isArray(parentContainer) && typeof lastSegment === "number") {
        parentContainer.splice(lastSegment, 1);
        return;
    }

    const parentRecord = parentContainer as Record<string | number, unknown>;
    const currentValue = parentRecord[lastSegment];

    parentRecord[lastSegment] = Array.isArray(currentValue) ? [] : null;
}

function buildPayloadForSave() {
    const resourceDataClone = structuredClone(resourceData);
    const widgetDirtyStatesClone = structuredClone(widgetDirtyStates);

    const pathsToRemove = sortPathsForSafeRemoval(
        Array.from(softDeletedValuePaths.value.values()),
    );

    for (const pathToRemove of pathsToRemove) {
        removeValueAtPath(resourceDataClone, pathToRemove);
        removeValueAtPath(widgetDirtyStatesClone, pathToRemove);
    }

    return pruneResourceData(
        resourceDataClone as unknown as ResourceData,
        widgetDirtyStatesClone as unknown as WidgetDirtyStates,
    );
}

const selectedTileData = computed<TileData | undefined>(() => {
    if (!selectedTilePath.value) {
        return undefined;
    }

    const tileData = getValueFromPath(resourceData, selectedTilePath.value);

    if (!tileData || Array.isArray(tileData)) {
        return undefined;
    }

    return tileData as unknown as TileData;
});

watchEffect(async () => {
    try {
        const modularReportResource = await fetchModularReportResource({
            graphSlug,
            resourceId: resourceInstanceId,
            fillBlanks: true,
        });

        originalResourceData.value = readonly(
            structuredClone({ ...modularReportResource }),
        );

        Object.assign(resourceData, modularReportResource);

        replaceReactiveRecord(
            widgetDirtyStates,
            generateWidgetDirtyStates(modularReportResource),
        );

        unsavedTileKeys.value.clear();
        softDeletedTileKeys.value = new Set<string>();
        softDeletedValuePaths.value = new Map<string, Array<string | number>>();
    } catch (error) {
        apiError.value = error as Error;
    } finally {
        isLoading.value = false;
    }
});

watch(
    [selectedNodegroupAlias, selectedTileId, selectedTilePath, isLoading],
    () => {
        if (isLoading.value) {
            return;
        }

        if (!selectedTilePath.value && selectedNodegroupAlias.value) {
            const aliasedTileData: NodeData | NodegroupData =
                resourceData.aliased_data[selectedNodegroupAlias.value];

            const pathSegments: Array<string | number> = [
                "aliased_data",
                selectedNodegroupAlias.value,
            ];

            if (Array.isArray(aliasedTileData) && selectedTileId.value) {
                const tileIndex = aliasedTileData.findIndex(
                    (tile) => tile.tileid === selectedTileId.value,
                );

                if (tileIndex >= 0) {
                    pathSegments.push(tileIndex);
                }
            }

            setSelectedTilePath(pathSegments);
        }
    },
);

watch(createTileRequestId, async () => {
    if (isLoading.value) {
        return;
    }

    const requestedNodegroupAlias = createTileRequestedNodegroupAlias.value;

    if (!requestedNodegroupAlias) {
        return;
    }

    const requestedNodegroupValuePath =
        createTileRequestedTilePath?.value ?? null;

    let nodegroupValuePath: Array<string | number> = [
        "aliased_data",
        requestedNodegroupAlias,
    ];

    if (requestedNodegroupValuePath && requestedNodegroupValuePath.length > 0) {
        nodegroupValuePath = requestedNodegroupValuePath;
    }

    apiError.value = null;

    try {
        isLoading.value = true;

        const blankTile = await fetchModularReportBlankTile(
            graphSlug,
            requestedNodegroupAlias,
        );

        const isCardinalityN = isCardinalityNNodegroup(requestedNodegroupAlias);

        const createdTilePath = insertAtNodegroupPath({
            targetRoot: resourceData,
            nodegroupValuePath,
            valueToInsert: blankTile,
            isCardinalityN,
        });

        if (!createdTilePath) {
            apiError.value = new Error($gettext("The tile already exists."));
            return;
        }

        setSelectedTileId(blankTile.tileid ?? null);
        setSelectedTilePath(createdTilePath);

        unsavedTileKeys.value.add(
            blankTile.tileid
                ? blankTile.tileid
                : JSON.stringify(createdTilePath),
        );

        const newTileDirtyStates = buildDirtyStatesForNewTile(blankTile);

        const createdDirtyPath = insertAtNodegroupPath({
            targetRoot: widgetDirtyStates,
            nodegroupValuePath,
            valueToInsert: newTileDirtyStates,
            isCardinalityN,
        });

        if (!createdDirtyPath) {
            setValueAtPath(
                widgetDirtyStates,
                nodegroupValuePath,
                newTileDirtyStates,
            );
        }
    } catch (error) {
        apiError.value = error as Error;
    } finally {
        isLoading.value = false;
    }
});

function onUpdateTileData(updatedTileData: TileData) {
    const currentTileValue = getValueFromPath(
        resourceData,
        selectedTilePath.value,
    )!;

    const tileDirtyStates = getValueFromPath(
        widgetDirtyStates,
        selectedTilePath.value,
    )!;

    const originalTileValueFromSnapshot = getValueFromPath(
        originalResourceData.value,
        selectedTilePath.value,
    );

    for (const [tileKey, tileValue] of Object.entries(updatedTileData)) {
        currentTileValue[tileKey] = tileValue;
    }

    const currentAliasedData = currentTileValue[
        "aliased_data"
    ] as AliasedTileData["aliased_data"];

    const dirtyAliasedData = (
        tileDirtyStates as { aliased_data: Record<string, unknown> }
    ).aliased_data;

    if (unsavedTileKeys.value.has(selectedTileKey.value)) {
        for (const nodeAlias of Object.keys(currentAliasedData)) {
            if (typeof dirtyAliasedData[nodeAlias] === "boolean") {
                dirtyAliasedData[nodeAlias] = true;
            } else if (dirtyAliasedData[nodeAlias] == null) {
                dirtyAliasedData[nodeAlias] = true;
            }
        }
        return;
    }

    if (!originalTileValueFromSnapshot) {
        return;
    }

    const originalAliasedData = originalTileValueFromSnapshot[
        "aliased_data"
    ] as AliasedTileData["aliased_data"];

    for (const [nodeAlias, aliasedData] of Object.entries(currentAliasedData)) {
        if (typeof dirtyAliasedData[nodeAlias] !== "boolean") {
            continue;
        }

        dirtyAliasedData[nodeAlias] = !isEqual(
            aliasedData,
            originalAliasedData[nodeAlias],
        );
    }
}

function onUpdateWidgetFocusStates(
    updatedWidgetFocusStates: Record<string, boolean>,
) {
    const focusedNodeAlias = Object.keys(updatedWidgetFocusStates).find(
        (nodeAliasKey) => updatedWidgetFocusStates[nodeAliasKey] === true,
    );

    if (!focusedNodeAlias) {
        return;
    }

    setSelectedNodeAlias(focusedNodeAlias);
}

function onToggleSoftDelete(payload: SoftDeletePayload) {
    const nextSoftDeletedTileKeys = new Set<string>(softDeletedTileKeys.value);
    const nextSoftDeletedValuePaths = new Map<string, Array<string | number>>(
        softDeletedValuePaths.value,
    );

    if (payload.nextIsSoftDeleted) {
        nextSoftDeletedTileKeys.add(payload.softDeleteKey);
        nextSoftDeletedValuePaths.set(
            payload.softDeleteKey,
            payload.nodegroupValuePath,
        );

        if (selectedTileKey.value === payload.softDeleteKey) {
            setSelectedNodeAlias(null);
            setSelectedTileId(null);
            setSelectedTilePath(null);
        }
    } else {
        nextSoftDeletedTileKeys.delete(payload.softDeleteKey);
        nextSoftDeletedValuePaths.delete(payload.softDeleteKey);
    }

    softDeletedTileKeys.value = nextSoftDeletedTileKeys;
    softDeletedValuePaths.value = nextSoftDeletedValuePaths;
}

function onRequestUndoAllChanges() {
    confirm.require({
        message: $gettext(
            "Are you sure? This will undo all of your pending changes.",
        ),
        header: $gettext("Undo all changes"),
        icon: "pi pi-exclamation-triangle",
        acceptLabel: $gettext("Continue"),
        rejectLabel: $gettext("Cancel"),
        accept: () => onUndoAllChanges(),
    });
}

function onUndoAllChanges() {
    apiError.value = null;

    const snapshotResourceData = structuredClone(originalResourceData.value);

    replaceReactiveRecord(resourceData, snapshotResourceData);

    replaceReactiveRecord(
        widgetDirtyStates,
        generateWidgetDirtyStates(snapshotResourceData),
    );

    unsavedTileKeys.value.clear();
    softDeletedTileKeys.value = new Set<string>();
    softDeletedValuePaths.value = new Map<string, Array<string | number>>();

    setSelectedNodeAlias(null);
    setSelectedTileId(null);
    setSelectedTilePath(null);
}

function onSave() {
    isLoading.value = true;
    apiError.value = null;

    updateModularReportResource(
        graphSlug,
        resourceInstanceId,
        buildPayloadForSave(),
    )
        .then(async (updatedResource) => {
            void updatedResource;

            emit("save");

            // this is sloppy but `_updatedResource` does not have the option to fill in blanks
            const modularReportResource = await fetchModularReportResource({
                graphSlug,
                resourceId: resourceInstanceId,
                fillBlanks: true,
            });

            originalResourceData.value = readonly(
                structuredClone({ ...modularReportResource }),
            );

            Object.assign(resourceData, modularReportResource);

            replaceReactiveRecord(
                widgetDirtyStates,
                generateWidgetDirtyStates(modularReportResource),
            );

            unsavedTileKeys.value.clear();
            softDeletedTileKeys.value = new Set<string>();
            softDeletedValuePaths.value = new Map<
                string,
                Array<string | number>
            >();
        })
        .catch((error: Error) => {
            if (error.message.includes("This card requires")) {
                error.message = $gettext(
                    "A required field in the current card or a parent of this card is missing.  Please enter a value for that field and try saving again..",
                );
            } else if (error.message.includes("Tile Cardinality Error")) {
                error.message = $gettext("The tile already exists.");
            }
            apiError.value = error;
        })
        .finally(() => {
            isLoading.value = false;
        });
}
</script>

<template>
    <ConfirmDialog />

    <Message
        v-if="apiError"
        severity="error"
        class="error-message"
    >
        {{ apiError.message }}
    </Message>

    <div
        v-if="isLoading"
        class="loading-skeleton"
    >
        <div style="display: flex; gap: 1rem; align-items: center">
            <Skeleton height="2.5rem"></Skeleton>
            <Skeleton
                height="2.5rem"
                width="10rem"
            ></Skeleton>
        </div>
        <Skeleton height="2.5rem"></Skeleton>
        <Skeleton height="8rem"></Skeleton>
    </div>

    <template v-else>
        <div class="editor-layout">
            <Splitter
                layout="vertical"
                class="editor-splitter"
                style="overflow: hidden"
            >
                <SplitterPanel class="top-panel">
                    <div style="margin: 1rem">
                        <GenericCard
                            v-if="
                                selectedTileData && !isSelectedTileSoftDeleted
                            "
                            :mode="EDIT"
                            :nodegroup-alias="selectedNodegroupAlias!"
                            :graph-slug="graphSlug"
                            :resource-instance-id="resourceInstanceId"
                            :selected-node-alias="selectedNodeAlias"
                            :should-show-form-buttons="false"
                            :tile-id="selectedTileId"
                            :tile-data="selectedTileData"
                            @update:widget-focus-states="
                                onUpdateWidgetFocusStates($event)
                            "
                            @update:tile-data="onUpdateTileData($event)"
                        />
                    </div>
                </SplitterPanel>

                <SplitterPanel class="bottom-panel">
                    <div class="bottom-panel-scroll">
                        <DataTree
                            :resource-data="resourceData"
                            :widget-dirty-states="widgetDirtyStates"
                            :soft-deleted-tile-keys="softDeletedTileKeys"
                            @toggle-soft-delete="onToggleSoftDelete($event)"
                        />
                    </div>
                </SplitterPanel>
            </Splitter>

            <div class="editor-footer">
                <div class="editor-footer-actions">
                    <Button
                        severity="danger"
                        variant="outlined"
                        icon="pi pi-undo"
                        label="Undo all changes"
                        @click="onRequestUndoAllChanges"
                    />

                    <Button
                        severity="success"
                        icon="pi pi-save"
                        label="Save all changes"
                        @click="onSave"
                    />
                </div>
            </div>
        </div>
    </template>
</template>

<style scoped>
.error-message,
.loading-skeleton {
    margin: 1rem;
}

.editor-layout {
    height: 100%;
    display: flex;
    flex-direction: column;
    min-height: 0;
}

.editor-splitter {
    flex: 1;
    min-height: 0;
}

.top-panel {
    display: flex;
    flex-direction: column;
    min-height: 0;
    overflow: auto;
}

.bottom-panel {
    display: flex;
    flex-direction: column;
    min-height: 0;
    overflow: hidden;
}

.bottom-panel-scroll {
    flex: 1;
    min-height: 0;
    overflow: auto;
}

.editor-footer {
    border-top: 0.125rem solid var(--p-content-border-color);
    padding: 0.75rem 1rem;
    background: var(--surface-0);
}

.editor-footer-actions {
    display: flex;
    gap: 0.5rem;
    justify-content: flex-end;
}

:deep(.editor-footer-actions .pi) {
    font-size: 1.4rem !important;
}

.loading-skeleton {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

:deep(.p-splitter) {
    height: 100%;
}

:deep(.p-splitter-panel) {
    min-height: 0;
}
</style>
