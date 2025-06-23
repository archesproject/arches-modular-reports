<script setup lang="ts">
import { inject, onMounted, ref } from "vue";

import Message from "primevue/message";
import ProgressSpinner from "primevue/progressspinner";

import { fetchModularReportResource } from "@/arches_modular_reports/ModularReport/api.ts";
import CardEditor from "@/arches_modular_reports/ModularReport/components/ResourceEditor/components/CardEditor/CardEditor.vue";
import DataTree from "@/arches_modular_reports/ModularReport/components/ResourceEditor/components/DataTree.vue";

import type { ResourceData } from "@/arches_modular_reports/ModularReport/types.ts";

const resourceId = inject("resourceInstanceId") as string;
const resourceData = ref<ResourceData | undefined>();
const isLoading = ref(true);

onMounted(async () => {
    try {
        resourceData.value = await fetchModularReportResource({
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
