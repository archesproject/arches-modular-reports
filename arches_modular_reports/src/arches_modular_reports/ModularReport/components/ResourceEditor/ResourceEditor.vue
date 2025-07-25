<script setup lang="ts">
import { computed, inject, reactive, ref, watchEffect } from "vue";

import Message from "primevue/message";
import Skeleton from "primevue/skeleton";

import DataTree from "@/arches_modular_reports/ModularReport/components/ResourceEditor/components/DataTree.vue";
import GenericCard from "@/arches_component_lab/generics/GenericCard/GenericCard.vue";

import { fetchModularReportResource } from "@/arches_modular_reports/ModularReport/api.ts";

import { EDIT } from "@/arches_component_lab/widgets/constants.ts";

import type { Ref } from "vue";
import type {
    NodeData,
    NodegroupData,
    ResourceData,
    TileData,
} from "@/arches_modular_reports/ModularReport/types.ts";

const { selectedNodegroupAlias } = inject("selectedNodegroupAlias") as {
    selectedNodegroupAlias: Ref<string | null>;
};
const { selectedTileId } = inject("selectedTileId") as {
    selectedTileId: Ref<string | null | undefined>;
};

const graphSlug = inject<string>("graphSlug")!;
const resourceInstanceId = inject<string>("resourceInstanceId")!;

const emit = defineEmits(["save"]);

const resourceData = reactive<ResourceData>({} as ResourceData);
const configurationError = ref<Error | null>(null);
const isLoading = ref(true);

watchEffect(async () => {
    try {
        Object.assign(
            resourceData,
            await fetchModularReportResource({
                graphSlug,
                resourceId: resourceInstanceId,
                fillBlanks: true,
            }),
        );
    } catch (error) {
        configurationError.value = error as Error;
    } finally {
        isLoading.value = false;
    }
});

const selectedTileData = computed<TileData | undefined>(() => {
    const selectedNodegroupAliasedTileData: NodeData | NodegroupData =
        resourceData.aliased_data[selectedNodegroupAlias.value!];

    if (Array.isArray(selectedNodegroupAliasedTileData)) {
        return selectedNodegroupAliasedTileData.find(
            (tileDatum) => tileDatum.tileid === selectedTileId.value,
        );
    }
    return selectedNodegroupAliasedTileData as TileData;
});

function onUpdateTileData(updatedTileData: TileData) {
    const selectedNodegroupAliasedTileData: NodeData | NodegroupData =
        resourceData.aliased_data[selectedNodegroupAlias.value!];

    if (Array.isArray(selectedNodegroupAliasedTileData)) {
        const selectedTileDatum = selectedNodegroupAliasedTileData.find(
            (tileDatum) => tileDatum.tileid === selectedTileId.value,
        );

        if (selectedTileDatum) {
            Object.assign(selectedTileDatum, updatedTileData);
        }
    } else {
        Object.assign(selectedNodegroupAliasedTileData, updatedTileData);
    }
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
        <GenericCard
            v-if="selectedNodegroupAlias && graphSlug"
            ref="defaultCard"
            :mode="EDIT"
            :nodegroup-alias="selectedNodegroupAlias"
            :graph-slug="graphSlug"
            :resource-instance-id="resourceInstanceId"
            :tile-id="selectedTileId"
            :tile-data="selectedTileData"
            @save="
                console.log('save', $event);
                emit('save', $event);
            "
            @update:widget-dirty-states="
                console.log('update:widgetDirtyStates', $event)
            "
            @update:tile-data="onUpdateTileData($event)"
        />
        <DataTree :resource-data="resourceData" />
    </template>
</template>
