<script setup lang="ts">
import { inject } from "vue";

import DefaultCard from "@/arches_component_lab/cards/DefaultCard/DefaultCard.vue";

const graphSlug = inject<string>("graphSlug")!;

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
        mode="edit"
        :nodegroup-alias="selectedNodegroupAlias"
        :graph-slug="graphSlug"
        :tile-id="selectedTileId"
        @update:is-dirty="console.log('update:isDirty', $event)"
        @update:tile-data="console.log('update:tileData', $event)"
    />
</template>
