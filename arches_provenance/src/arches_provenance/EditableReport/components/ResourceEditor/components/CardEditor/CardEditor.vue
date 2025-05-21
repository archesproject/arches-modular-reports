<script setup lang="ts">
import { inject } from "vue";

import DefaultCard from "@/arches_component_lab/cards/DefaultCard.vue";

const { selectedNodegroupGroupingNodeAlias } = inject(
    "selectedNodegroupGroupingNodeAlias",
) as {
    selectedNodegroupGroupingNodeAlias: string | null;
};
const graphSlug = inject("graphSlug") as string;

// const { selectedTileId } = inject("selectedTileId") as {
//     selectedTileId: string | null;
// };
// const resourceInstanceId = inject("resourceInstanceId") as string;
</script>

<template>
    <DefaultCard
        v-if="selectedNodegroupGroupingNodeAlias && graphSlug"
        mode="edit"
        :nodegroup-grouping-node-alias="selectedNodegroupGroupingNodeAlias"
        :graph-slug="graphSlug"
    />
</template>
