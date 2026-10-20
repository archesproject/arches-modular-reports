<script setup lang="ts">
import { useGettext } from "vue3-gettext";

import ReportPlaceholder from "@/arches_modular_reports/ResourceReport/components/ReportPlaceholder.vue";

import type {
    ReportData,
    ReportWorkspaceConfig,
} from "@/arches_modular_reports/ResourceReport/types.ts";

defineProps<{
    workspaceConfig: ReportWorkspaceConfig;
    reportData: ReportData;
}>();

const { $gettext } = useGettext();
</script>

<template>
    <ReportPlaceholder
        icon="pi pi-sitemap"
        :message="$gettext('Graph view — coming soon')"
    />
</template>
