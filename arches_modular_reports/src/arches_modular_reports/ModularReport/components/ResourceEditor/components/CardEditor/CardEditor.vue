<script setup lang="ts">
import { inject } from "vue";

const { selectedNodegroupAlias } = inject("selectedNodegroupAlias") as {
    selectedNodegroupAlias: string | null;
};
const { selectedTileId } = inject("selectedTileId") as {
    selectedTileId: string | null;
};
</script>

<template>
    <p>Selected Nodegroup: {{ selectedNodegroupAlias }}</p>
    <p>Selected Tile: {{ selectedTileId ?? "blank" }}</p>
    <!-- todo: determine if we need other info, like parent tile id? -->
    <!-- those three pieces of info to start to look like a whole Tile? -->
</template>
