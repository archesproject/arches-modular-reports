<script setup lang="ts">
import { inject, onMounted, ref } from "vue";

import Message from "primevue/message";
import ProgressSpinner from "primevue/progressspinner";

import { fetchProvenanceResource } from "@/arches_provenance/EditableReport/api.ts";
import CardEditor from "@/arches_provenance/EditableReport/components/ResourceEditor/components/CardEditor/CardEditor.vue";
import DataTree from "@/arches_provenance/EditableReport/components/ResourceEditor/components/DataTree.vue";

import type { ResourceData } from "@/arches_provenance/EditableReport/components/ResourceEditor/types.ts";

const resourceId = inject("resourceInstanceId") as string;
const resourceData = ref<ResourceData | undefined>();
const isLoading = ref(true);

onMounted(async () => {
    try {
        resourceData.value = await fetchProvenanceResource({
            resourceId,
            fillBlanks: true,
        });
    } finally {
        isLoading.value = false;
    }
});
</script>

<template>
    <ProgressSpinner v-if="isLoading" />
    <Message
        v-else-if="!resourceData"
        severity="error"
        style="width: fit-content"
    >
        {{ $gettext("Unable to fetch resource") }}
    </Message>
    <template v-else>
        <CardEditor />
        <DataTree :resource-data="resourceData" />
    </template>
</template>
