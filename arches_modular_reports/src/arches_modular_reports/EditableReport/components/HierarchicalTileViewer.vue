<script setup lang="ts">
import { inject, onMounted, ref } from "vue";
import { useGettext } from "vue3-gettext";

import Message from "primevue/message";

import {
    fetchProvenanceTile,
    fetchUserPermissions,
} from "@/arches_modular_reports/EditableReport/api.ts";
import ChildTile from "@/arches_modular_reports/EditableReport/components/ChildTile.vue";

import type { TileData } from "@/arches_modular_reports/EditableReport/types";

const {
    nodegroupAlias,
    tileId,
    customLabels,
    showEmptyNodes = true,
} = defineProps<{
    nodegroupAlias: string;
    tileId: string;
    customLabels?: Record<string, string>;
    showEmptyNodes: boolean;
}>();

const { $gettext } = useGettext();

const isLoading = ref(true);
const hasLoadingError = ref(false);
const tileData = ref<TileData>();
const userIsRdmAdmin = ref(false);

const resourceInstanceId = inject("resourceInstanceId") as string;

async function fetchData() {
    try {
        await Promise.all([
            fetchProvenanceTile(
                nodegroupAlias,
                tileId,
                resourceInstanceId,
            ).then((data) => (tileData.value = data)),
            fetchUserPermissions(["RDM Administrator"]).then((data) => {
                userIsRdmAdmin.value = data["RDM Administrator"];
            }),
        ]);
        hasLoadingError.value = false;
    } catch {
        hasLoadingError.value = true;
    }
    isLoading.value = false;
}

onMounted(fetchData);
</script>

<template>
    <ChildTile
        v-if="tileData"
        :data="tileData"
        :depth="1"
        :custom-labels
        :show-empty-nodes
        :user-is-rdm-admin="userIsRdmAdmin"
    />
    <Message
        v-if="hasLoadingError"
        severity="error"
    >
        {{ $gettext("Unable to fetch resource") }}
    </Message>
    <p
        v-else-if="!isLoading && !tileData"
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
