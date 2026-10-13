<script setup lang="ts">
import { useGettext } from "vue3-gettext";

import ReportPlaceholder from "@/arches_modular_reports/ResourceReport/components/ReportPlaceholder.vue";

const { $gettext } = useGettext();
</script>

<template>
    <ReportPlaceholder
        icon="pi pi-sitemap"
        :message="$gettext('A graph view of this resource is coming soon.')"
    />
</template>
