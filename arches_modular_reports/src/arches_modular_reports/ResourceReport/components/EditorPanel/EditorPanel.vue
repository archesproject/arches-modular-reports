<script setup lang="ts">
import { onMounted, onUnmounted, watch } from "vue";

import EditorForm from "@/arches_modular_reports/ResourceReport/components/EditorPanel/components/EditorForm.vue";

import { useAsideWidening } from "@/arches_modular_reports/ResourceReport/composables/useAsideWidening.ts";
import { useReportData } from "@/arches_modular_reports/ResourceReport/composables/useReportData.ts";

import type { ComponentNode } from "@/arches_modular_reports/ResourceReport/types.ts";

defineProps<{
    component: ComponentNode;
}>();

const reportData = useReportData();
const isAsideWidened = useAsideWidening();

let unregisterEditor = (): void => undefined;

watch(
    () => reportData.value.editor.target,
    (target) => {
        if (isAsideWidened !== null) {
            isAsideWidened.value = target !== null;
        }
    },
    { immediate: true },
);

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
    display: flex;
    flex-direction: column;
    overflow: hidden;
    background: var(--resource-report-panel-background);
}
</style>
