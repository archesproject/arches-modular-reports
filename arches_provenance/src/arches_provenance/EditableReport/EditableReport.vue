<script setup lang="ts">
import { onMounted, ref } from "vue";
import { fetchReportConfig } from "@/arches_provenance/EditableReport/api.ts";

const resourceId = window.location.href.split("/").reverse()[0];
const config = ref({ name: "Loading..." });

onMounted(async () => {
    config.value = await fetchReportConfig(resourceId);
});
</script>

<template>
    <div style="display: flex; flex-direction: row">
        <pre style="width: 33%; text-wrap: auto">{{ config }}</pre>
        <h1>{{ config.name }}</h1>
    </div>
</template>
