<script setup lang="ts">
import type { SectionContent } from "@/arches_provenance/EditableReport/types";

const { component } = defineProps<{
    component: SectionContent;
    resourceInstanceId: string;
}>();
</script>

<template>
    <pre>{{ component.config }}</pre>
</template>
