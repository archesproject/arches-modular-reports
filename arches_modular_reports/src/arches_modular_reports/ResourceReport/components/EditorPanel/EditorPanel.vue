<script setup lang="ts">
import { onMounted, onUnmounted } from "vue";

import EditorForm from "@/arches_modular_reports/ResourceReport/components/EditorPanel/components/EditorForm.vue";

import { useReportData } from "@/arches_modular_reports/ResourceReport/composables/useReportData.ts";

import type { ComponentNode } from "@/arches_modular_reports/ResourceReport/types.ts";

defineProps<{
    component: ComponentNode;
}>();

const reportData = useReportData();

let unregisterEditor = (): void => undefined;

onMounted(() => {
    unregisterEditor = reportData.value.editor.register();
});

onUnmounted(() => {
    unregisterEditor();
});
</script>

<template>
    <div
        v-if="reportData.editor.target"
        class="editor-panel-overlay"
    >
        <EditorForm :target="reportData.editor.target" />
    </div>
</template>

<style scoped>
.editor-panel-overlay {
    position: absolute;
    inset: 0;
    z-index: 1;
    overflow: auto;
    background: var(--p-resource-report-aside-background);
}
</style>
