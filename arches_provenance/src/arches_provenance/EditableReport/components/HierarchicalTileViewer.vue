<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useGettext } from "vue3-gettext";

import Message from "primevue/message";

import { fetchChildTileData } from "@/arches_provenance/EditableReport/api.ts";
import ChildTile from "@/arches_provenance/EditableReport/components/ChildTile.vue";

import type { LabelBasedTile } from "@/arches_provenance/EditableReport/types";

const props = defineProps<{
    tileId: string;
    customLabels?: Record<string, string>;
}>();

const { $gettext } = useGettext();

const isLoading = ref(true);
const hasLoadingError = ref(false);
const childTileData = ref<LabelBasedTile[]>([]);

async function fetchData() {
    try {
        childTileData.value = await fetchChildTileData(props.tileId);
        hasLoadingError.value = false;
    } catch {
        hasLoadingError.value = true;
    }
    isLoading.value = false;
}

onMounted(fetchData);
</script>

<template>
    <template
        v-for="child in childTileData"
        :key="Object.values(child)[1]['@tile_id']"
    >
        <ChildTile
            :data="child"
            :depth="1"
            :custom-labels
        />
    </template>
    <Message
        v-if="hasLoadingError"
        severity="error"
    >
        {{ $gettext("Unable to fetch resource") }}
    </Message>
    <p
        v-else-if="!isLoading && !childTileData.length"
        style="padding: 0 4.25rem; margin-bottom: 0"
    >
        {{ $gettext("No further data found") }}
    </p>
</template>

<style scoped>
.p-message-error {
    margin-left: 4rem;
    display: inline-flex;
}
</style>
