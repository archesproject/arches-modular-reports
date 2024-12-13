<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useGettext } from "vue3-gettext";

import { useToast } from "primevue/usetoast";

import { fetchChildTileData } from "@/arches_provenance/EditableReport/api.ts";
import { DEFAULT_ERROR_TOAST_LIFE } from "@/arches_provenance/constants.ts";
import ChildTile from "@/arches_provenance/EditableReport/components/ChildTile.vue";

import type { LabelBasedTile } from "@/arches_provenance/EditableReport/types";

const props = defineProps<{ tileId: string }>();

const toast = useToast();
const { $gettext } = useGettext();

const isLoading = ref(true);
const childTileData = ref<LabelBasedTile[]>([]);

async function fetchData() {
    try {
        childTileData.value = await fetchChildTileData(props.tileId);
    } catch (error) {
        toast.add({
            severity: "error",
            life: DEFAULT_ERROR_TOAST_LIFE,
            summary: $gettext("Unable to fetch resource"),
            detail: error instanceof Error ? error.message : String(error),
        });
        throw error;
    } finally {
        isLoading.value = false;
    }
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
        />
    </template>
    <p
        v-if="!isLoading && !childTileData.length"
        style="padding: 0 4.25rem; margin-bottom: 0"
    >
        {{ $gettext("No further data found") }}
    </p>
</template>
