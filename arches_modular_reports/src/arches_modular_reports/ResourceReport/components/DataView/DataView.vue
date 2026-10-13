<script setup lang="ts">
import { useGettext } from "vue3-gettext";

import ReportPlaceholder from "@/arches_modular_reports/ResourceReport/components/ReportPlaceholder/ReportPlaceholder.vue";

const { $gettext } = useGettext();
</script>

<template>
    <ReportPlaceholder
        icon="pi pi-database"
        :message="$gettext('The data browser is not available yet.')"
    />
</template>
