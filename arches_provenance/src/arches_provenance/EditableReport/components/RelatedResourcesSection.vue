<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useGettext } from "vue3-gettext";

import { useToast } from "primevue/usetoast";

import { fetchRelatedResourceData } from "@/arches_provenance/EditableReport/api.ts";
import { DEFAULT_ERROR_TOAST_LIFE } from "@/arches_provenance/constants.ts";

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

const toast = useToast();
const { $gettext } = useGettext();

onMounted(async () => {
    try {
        relatedResources.value = await fetchRelatedResourceData(
            resourceInstanceId,
            component.config.graph_id,
            component.config.additional_nodes,
            rowsPerPage.value,
            page.value,
            sort.value,
            direction.value,
        );
    } catch (error) {
        toast.add({
            severity: "error",
            life: DEFAULT_ERROR_TOAST_LIFE,
            summary: $gettext("Unable to fetch related resources"),
            detail: error instanceof Error ? error.message : undefined,
        });
    }
});
</script>

<template>
    <pre>{{ relatedResources }}</pre>
</template>
