<script setup lang="ts">
import { fetchChildTileData } from "@/arches_provenance/EditableReport/api.ts";

import ChildTile from "@/arches_provenance/EditableReport/components/ChildTile.vue";

const props = defineProps<{ tileId: string }>();

const childTileData = await fetchChildTileData(props.tileId);
</script>

<template>
    <template
        v-for="child in childTileData"
        :key="Object.values(child)[1]['@tile_id']"
    >
        <ChildTile
            :data="child"
            :depth="1"
        />
    </template>
</template>
