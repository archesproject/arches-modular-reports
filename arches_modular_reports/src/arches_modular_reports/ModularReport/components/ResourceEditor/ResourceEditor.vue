<script setup lang="ts">
import {
    computed,
    inject,
    reactive,
    ref,
    shallowRef,
    watchEffect,
    readonly,
    toRaw,
} from "vue";

import Message from "primevue/message";
import Skeleton from "primevue/skeleton";
import Splitter from "primevue/splitter";
import SplitterPanel from "primevue/splitterpanel";

import DataTree from "@/arches_modular_reports/ModularReport/components/ResourceEditor/components/DataTree.vue";
import GenericCard from "@/arches_component_lab/generics/GenericCard/GenericCard.vue";

import { fetchModularReportResource } from "@/arches_modular_reports/ModularReport/api.ts";
import { findTileInTileTree } from "@/arches_modular_reports/ModularReport/utils.ts";

import { EDIT } from "@/arches_component_lab/widgets/constants.ts";

import type { Ref } from "vue";
import type {
    ResourceData,
    TileData,
} from "@/arches_modular_reports/ModularReport/types.ts";

import type { WidgetDirtyStates } from "@/arches_modular_reports/ModularReport/components/ResourceEditor/types.ts";
import type {
    AliasedData,
    AliasedTileData,
} from "@/arches_component_lab/types";

const { selectedNodegroupAlias } = inject("selectedNodegroupAlias") as {
    selectedNodegroupAlias: Ref<string | null>;
};
const { selectedTileId } = inject("selectedTileId") as {
    selectedTileId: Ref<string | null | undefined>;
};
const graphSlug = inject<string>("graphSlug")!;
const resourceInstanceId = inject<string>("resourceInstanceId")!;

const emit = defineEmits(["save", "reset"]);

const selectedNodeAlias = ref<string | null>(null);

const resourceData = reactive<ResourceData>({} as ResourceData);
const originalResourceData = shallowRef<Readonly<ResourceData>>(
    {} as ResourceData,
);

const widgetDirtyStates = reactive<WidgetDirtyStates>({});
const configurationError = ref<Error | null>(null);
const isLoading = ref(true);

const selectedTileData = computed<TileData | undefined>(() => {
    if (selectedTileId.value) {
        return findTileInTileTree(resourceData, selectedTileId.value);
    }
    return undefined;
});

const selectedTileWidgetDirtyStates = computed<Record<string, boolean>>(() => {
    const tileKey = String(selectedTileId.value);
    const tileWidgetDirtyStates = widgetDirtyStates[
        selectedNodegroupAlias.value!
    ] as Record<string, boolean> | undefined;
    return tileWidgetDirtyStates?.[tileKey] ?? {};
});

watchEffect(async () => {
    try {
        const modularReportResource = await fetchModularReportResource({
            graphSlug,
            resourceId: resourceInstanceId,
            fillBlanks: true,
        });
        Object.assign(resourceData, modularReportResource);
        originalResourceData.value = readonly(
            structuredClone({ ...modularReportResource }),
        );

        generateWidgetDirtyStateMap(modularReportResource.aliased_data);
    } catch (error) {
        configurationError.value = error as Error;
    } finally {
        isLoading.value = false;
    }
});

function generateWidgetDirtyStateMap(aliasedData: AliasedData): void {
    for (const [key, data] of Object.entries(aliasedData)) {
        let aliasedTileData = data;

        if (!Array.isArray(aliasedTileData)) {
            aliasedTileData = [data as AliasedTileData];
        }

        const dirtyStates = (widgetDirtyStates[key] ??=
            {}) as WidgetDirtyStates;

        for (const aliasedTileDatum of aliasedTileData as AliasedTileData[]) {
            const dirtyStateKey = aliasedTileDatum.tileid ?? "null";
            const dirtyState = (dirtyStates[dirtyStateKey] ??=
                {}) as WidgetDirtyStates;

            for (const childAliasKey of Object.keys(
                aliasedTileDatum.aliased_data,
            )) {
                dirtyState[childAliasKey] = false;
            }
        }
    }
}

function onReset(_tileData: TileData): void {
    const nodegroupAliasKey = selectedNodegroupAlias.value!;
    const originalTileData = toRaw(originalResourceData.value).aliased_data[
        nodegroupAliasKey
    ];
    const currentTileData = resourceData.aliased_data[nodegroupAliasKey]!;

    // Single-tile nodegroup
    if (!Array.isArray(originalTileData)) {
        Object.assign(currentTileData, structuredClone(originalTileData));
    } else {
        // Multi-tile nodegroup
        const tiles = currentTileData as AliasedTileData[];
        const currentTileId = selectedTileId.value!;
        const originalTileDatum = originalTileData.find(
            (tileDatum) => tileDatum.tileid === currentTileId,
        )!;

        const indexOfTile = tiles.findIndex(
            (tileDatum) => tileDatum.tileid === currentTileId,
        );
        tiles.splice(indexOfTile, 1, structuredClone(originalTileDatum));
    }

    emit("reset", {
        selectedNodegroupAlias: nodegroupAliasKey,
        tileid: selectedTileId.value,
    });
}

function onSave(tileData: TileData) {
    emit("save", tileData);
}

function onUpdateTileData(updatedTileData: TileData) {
    if (selectedTileId.value) {
        const selectedTileDatum = findTileInTileTree(
            resourceData,
            selectedTileId.value,
        );
        Object.assign(selectedTileDatum, updatedTileData);
    } else {
        throw new Error("Missing tile id for update");
    }
}

function onUpdateWidgetDirtyStates(
    updatedWidgetDirtyStates: WidgetDirtyStates,
) {
    const nodegroupDirtyStates = widgetDirtyStates[
        selectedNodegroupAlias.value!
    ] as WidgetDirtyStates;
    Object.assign(
        nodegroupDirtyStates[selectedTileId.value!],
        updatedWidgetDirtyStates,
    );
}

function onUpdateWidgetFocusStates(
    updatedWidgetFocusStates: Record<string, boolean>,
) {
    for (const [nodeAliasKey, isFocused] of Object.entries(
        updatedWidgetFocusStates,
    )) {
        if (isFocused) {
            selectedNodeAlias.value = nodeAliasKey;
            return;
        }
    }
    selectedNodeAlias.value = null;
}
</script>

<template>
    <Skeleton
        v-if="isLoading"
        style="height: 10rem"
    />
    <Message
        v-else-if="configurationError"
        severity="error"
    >
        {{ configurationError.message }}
    </Message>
    <template v-else>
        <Splitter
            style="height: 100%; height: stretch; width: stretch"
            layout="vertical"
        >
            <SplitterPanel
                style="
                    padding: var(--p-panel-toggleable-header-padding);
                    overflow: auto;
                "
            >
                <div>
                    <GenericCard
                        v-if="selectedNodegroupAlias && graphSlug"
                        ref="defaultCard"
                        :mode="EDIT"
                        :nodegroup-alias="selectedNodegroupAlias"
                        :graph-slug="graphSlug"
                        :resource-instance-id="resourceInstanceId"
                        :selected-node-alias="selectedNodeAlias"
                        :tile-id="selectedTileId"
                        :tile-data="selectedTileData"
                        :widget-dirty-states="selectedTileWidgetDirtyStates"
                        @save="onSave($event)"
                        @reset="onReset($event)"
                        @update:widget-focus-states="
                            onUpdateWidgetFocusStates($event)
                        "
                        @update:widget-dirty-states="
                            onUpdateWidgetDirtyStates($event)
                        "
                        @update:tile-data="onUpdateTileData($event)"
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
                    v-model:selected-node-alias="selectedNodeAlias"
                    :resource-data="resourceData"
                    :widget-dirty-states="widgetDirtyStates"
                />
            </SplitterPanel>
        </Splitter>
    </template>
</template>
