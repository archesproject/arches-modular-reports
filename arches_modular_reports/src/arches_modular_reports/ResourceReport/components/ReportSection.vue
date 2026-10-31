<script setup lang="ts">
import { computed } from "vue";

import { loadComponent } from "@/arches_modular_reports/ModularReport/utils.ts";
import { useReportData } from "@/arches_modular_reports/ResourceReport/composables/useReportData.ts";
import { localizeLabel } from "@/arches_modular_reports/ResourceReport/utils/localize-label.ts";

import type {
    ComponentNode,
    SectionConfig,
} from "@/arches_modular_reports/ResourceReport/types.ts";

const { component } = defineProps<{
    component: ComponentNode<SectionConfig>;
}>();

const reportData = useReportData();

const label = computed(() =>
    localizeLabel(
        component.config.label ?? null,
        reportData.value.context.language,
    ),
);

const childNodes = computed(() => component.config.components ?? []);
</script>

<template>
    <section class="report-section">
        <h3
            v-if="label"
            class="report-section-label"
        >
            <i
                v-if="component.config.icon"
                aria-hidden="true"
                class="report-section-icon"
                :class="component.config.icon"
            />
            <span>{{ label }}</span>
        </h3>
        <component
            :is="loadComponent(childNode.component)"
            v-for="(childNode, childIndex) in childNodes"
            :key="childIndex"
            :component="childNode"
        />
    </section>
</template>

<style scoped>
.report-section {
    display: flex;
    flex-direction: column;
}

.report-section > * + * {
    margin-block-start: 0.8rem;
}

.report-section > .field-folio + .field-folio {
    margin-block-start: 0;
}

.report-section:not(:first-child) {
    padding-block-start: 3.2rem;
}

.report-section-label {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    margin: 0;
    padding-block-end: 0.8rem;
    border-block-end: 0.1rem solid var(--p-content-border-color);
    color: var(--p-text-color);
    font-size: 1.7rem;
    font-weight: 700;
}

.report-section-icon {
    font-size: inherit;
}
</style>
