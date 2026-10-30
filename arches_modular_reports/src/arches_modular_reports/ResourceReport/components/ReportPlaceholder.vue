<script setup lang="ts">
import { computed } from "vue";

import { useReportData } from "@/arches_modular_reports/ResourceReport/composables/useReportData.ts";
import { localizeLabel } from "@/arches_modular_reports/ResourceReport/utils/localize-label.ts";

import type {
    ComponentNode,
    PlaceholderConfig,
} from "@/arches_modular_reports/ResourceReport/types.ts";

const { component } = defineProps<{
    component: ComponentNode<PlaceholderConfig>;
}>();

const reportData = useReportData();

const message = computed(() =>
    localizeLabel(
        component.config.message ?? null,
        reportData.value.context.language,
    ),
);
</script>

<template>
    <div class="report-placeholder">
        <div class="report-placeholder-message">
            <i
                v-if="component.config.icon"
                aria-hidden="true"
                :class="component.config.icon"
            />
            <span>{{ message }}</span>
        </div>
    </div>
</template>

<style scoped>
.report-placeholder {
    display: flex;
    justify-content: center;
    padding-block: 3.2rem;
    padding-inline: 1.6rem;
}

.report-placeholder-message {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 0.8rem;
    inline-size: 100%;
    max-inline-size: 48rem;
    padding-block: 3.2rem;
    padding-inline: 2.4rem;
    border: 0.1rem solid var(--p-content-border-color);
    border-radius: var(--p-content-border-radius);
    background: var(--p-content-background);
    color: var(--p-text-muted-color);
    font-size: 1.3rem;
    text-align: center;
}

.report-placeholder-message i {
    font-size: 2.8rem;
    opacity: 0.35;
}
</style>
