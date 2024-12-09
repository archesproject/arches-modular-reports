<script setup lang="ts">
import { fetchChildTileData } from "@/arches_provenance/EditableReport/api.ts";

const props = defineProps<{ tileId: string }>();

const childData = await fetchChildTileData(props.tileId);
</script>

<template>
    <pre>{{ childData }}</pre>
</template>
