<script setup lang="ts">
import { onMounted, ref } from "vue";

import { fetchRelatedResourceData } from "@/arches_provenance/EditableReport/api.ts";

import type { SectionContent } from "@/arches_provenance/EditableReport/types";

const { component, resourceInstanceId } = defineProps<{
    component: SectionContent;
    resourceInstanceId: string;
}>();

const relatedResources = ref({});
const rowsPerPage = ref(10);
const page = ref(1);
const sort = ref("widget_label");
const direction = ref("asc");

onMounted(async () => {
    await fetchRelatedResourceData(
        resourceInstanceId,
        component.config.graph_id,
        component.config.additional_nodes,
        rowsPerPage.value,
        page.value,
        sort.value,
        direction.value,
    ).then((data) => (relatedResources.value = data));
});
</script>

<template>
    <pre>{{ relatedResources }}</pre>
</template>
