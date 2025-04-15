<script setup lang="ts">
import { inject } from "vue";

const { selectedNodeAlias } = inject("selectedNodeAlias") as {
    selectedNodeAlias: string | null;
};
const { selectedTileId } = inject("selectedTileId") as {
    selectedTileId: string | null;
};
// const resourceInstanceId = inject("resourceInstanceId") as string;
</script>

<template>
    <p>Selected Node: {{ selectedNodeAlias }}</p>
    <p>Selected Tile: {{ selectedTileId }}</p>
</template>
