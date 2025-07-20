<script setup lang="ts">
import { inject } from "vue";

import DefaultCard from "@/arches_component_lab/cards/DefaultCard/DefaultCard.vue";

import { EDIT } from "@/arches_component_lab/widgets/constants.ts";

const graphSlug = inject<string>("graphSlug");
const resourceInstanceId = inject<string>("resourceInstanceId");

const { selectedNodegroupAlias } = inject("selectedNodegroupAlias") as {
    selectedNodegroupAlias: string | null;
};
const { selectedTileId } = inject("selectedTileId") as {
    selectedTileId: string | null | undefined;
};
</script>

<template>
    <DefaultCard
        v-if="selectedNodegroupAlias && graphSlug"
        :mode="EDIT"
        :nodegroup-alias="selectedNodegroupAlias"
        :graph-slug="graphSlug"
        :resource-instance-id="resourceInstanceId"
        :tile-id="selectedTileId"
        @update:widget-dirty-states="
            console.log('update:widgetDirtyStates', $event)
        "
        @update:tile-data="console.log('update:tileData', $event)"
    />
</template>
