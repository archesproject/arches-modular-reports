<script setup lang="ts">
import {
    computed,
    inject,
    reactive,
    ref,
    shallowRef,
    watchEffect,
    readonly,
    watch,
} from "vue";

import { isEqual } from "es-toolkit";

import Button from "primevue/button";
import Message from "primevue/message";
import Skeleton from "primevue/skeleton";
import Splitter from "primevue/splitter";
import SplitterPanel from "primevue/splitterpanel";

import DataTree from "@/arches_modular_reports/ModularReport/components/ResourceEditor/components/DataTree/DataTree.vue";
import GenericCard from "@/arches_component_lab/generics/GenericCard/GenericCard.vue";

import {
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
    ResourceData,
    TileData,
} from "@/arches_modular_reports/ModularReport/types.ts";

import type { WidgetDirtyStates } from "@/arches_modular_reports/ModularReport/components/ResourceEditor/types.ts";
import type { AliasedTileData } from "@/arches_component_lab/types";

const graphSlug = inject<string>("graphSlug")!;
const resourceInstanceId = inject<string>("resourceInstanceId")!;

const { selectedNodegroupAlias } = inject("selectedNodegroupAlias") as {
    selectedNodegroupAlias: Ref<string | null>;
};
const { selectedNodeAlias, setSelectedNodeAlias } = inject(
    "selectedNodeAlias",
) as {
    selectedNodeAlias: Ref<string | null>;
    setSelectedNodeAlias: (nodeAlias: string | null) => void;
};
const { selectedTileId } = inject("selectedTileId") as {
    selectedTileId: Ref<string | null | undefined>;
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
const widgetDirtyStates = reactive<WidgetDirtyStates>({});

const selectedTileData = computed<TileData | undefined>(function () {
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
        Object.assign(
            widgetDirtyStates,
            generateWidgetDirtyStates(modularReportResource),
        );
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

        // Derive selectedTilePath if not explicitly set
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

function onUpdateTileData(updatedTileData: TileData) {
    const currentTileValue = getValueFromPath(
        resourceData,
        selectedTilePath.value,
    )!;
    const originalTileValue = getValueFromPath(
        originalResourceData.value,
        selectedTilePath.value,
    )!;
    const tileDirtyStates = getValueFromPath(
        widgetDirtyStates,
        selectedTilePath.value,
    )!;

    // first update the current tile values, cannot do whole tile replacement because of reactivity
    for (const [tileKey, tileValue] of Object.entries(updatedTileData)) {
        currentTileValue[tileKey] = tileValue;
    }

    const currentAliasedData = currentTileValue[
        "aliased_data"
    ] as AliasedTileData["aliased_data"];
    const originalAliasedData = originalTileValue[
        "aliased_data"
    ] as AliasedTileData["aliased_data"];

    const dirtyAliasedData = (
        tileDirtyStates as { aliased_data: Record<string, boolean> }
    ).aliased_data;

    // then update the dirty states for each widget in the tile
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
        function (nodeAliasKey) {
            return updatedWidgetFocusStates[nodeAliasKey] === true;
        },
    );

    setSelectedNodeAlias(focusedNodeAlias ?? null);
}

function onSave() {
    isLoading.value = true;

    updateModularReportResource(
        graphSlug,
        resourceInstanceId,
        pruneResourceData(resourceData, widgetDirtyStates),
    )
        .then(async (_updatedResource) => {
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
            Object.assign(
                widgetDirtyStates,
                generateWidgetDirtyStates(modularReportResource),
            );
        })
        .catch((error) => {
            apiError.value = error as Error;
        })
        .finally(() => {
            isLoading.value = false;
        });
}
</script>

<template>
    <Skeleton
        v-if="isLoading"
        style="height: 10rem"
    />
    <Message
        v-else-if="apiError"
        severity="error"
    >
        {{ apiError.message }}
    </Message>
    <template v-else>
        <Splitter
            style="height: 100%; height: stretch; width: stretch"
            layout="vertical"
        >
            <SplitterPanel
                style="
                    padding: var(--p-panel-toggleable-header-padding);
                    overflow: hidden;
                    display: flex;
                    flex-direction: column;
                "
            >
                <div style="flex: 1; overflow: auto">
                    <GenericCard
                        v-if="selectedTileData"
                        ref="defaultCard"
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
                <div
                    style="
                        border-top: 1px solid
                            var(--p-panel-content-border-color);
                        padding: 0.5rem;
                        text-align: right;
                        display: flex;
                    "
                >
                    <Button
                        :label="$gettext('Save')"
                        icon="pi pi-check"
                        @click="onSave"
                    />
                </div>
            </SplitterPanel>
            <SplitterPanel
                style="
                    padding: var(--p-panel-toggleable-header-padding);
                    overflow: auto;
                "
            >
                <DataTree
                    :resource-data="resourceData"
                    :widget-dirty-states="widgetDirtyStates"
                />
            </SplitterPanel>
        </Splitter>
    </template>
</template>
