<script setup lang="ts">
import { computed } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";

import { useReportData } from "@/arches_modular_reports/ResourceReport/composables/useReportData.ts";
import { EMPTY_VALUE } from "@/arches_modular_reports/ResourceReport/constants.ts";
import { summaryRows } from "@/arches_modular_reports/ResourceReport/utils/summary-rows.ts";

import type {
    ComponentNode,
    KeyDataSummaryConfig,
} from "@/arches_modular_reports/ResourceReport/types.ts";

const { component } = defineProps<{
    component: ComponentNode<KeyDataSummaryConfig>;
}>();

const { $gettext } = useGettext();
const reportData = useReportData();

const rows = computed(() =>
    summaryRows(
        component.config.summary ?? [],
        reportData.value.resource.aliased_data,
        reportData.value.context.language,
    ).map((summaryRow) => ({
        nodeAlias: summaryRow.nodeAlias,
        label: summaryRow.label,
        value: summaryRow.values.join("; ") || EMPTY_VALUE,
    })),
);
</script>

<template>
    <section class="key-data-summary">
        <h3 class="key-data-summary-title">
            {{ $gettext("Key Data Summary") }}
        </h3>
        <p
            v-if="rows.length === 0"
            class="key-data-summary-empty"
        >
            {{ $gettext("No key data is configured for this report.") }}
        </p>
        <dl
            v-else
            class="key-data-summary-rows"
        >
            <div
                v-for="summaryRow in rows"
                :key="summaryRow.nodeAlias"
                class="key-data-summary-row"
            >
                <dt>
                    <Button
                        variant="link"
                        :label="summaryRow.label"
                        @click="
                            reportData.folioNavigation.jumpToNode(
                                summaryRow.nodeAlias,
                            )
                        "
                    />
                </dt>
                <dd>{{ summaryRow.value }}</dd>
            </div>
        </dl>
    </section>
</template>

<style scoped>
.key-data-summary {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    padding-block: 1.4rem;
    padding-inline: 1.6rem;
    border: 0.1rem solid var(--p-content-border-color);
    border-radius: 0.4rem;
    background: var(--p-content-background);
}

.key-data-summary-title {
    margin: 0;
    color: var(--p-text-muted-color);
    font-size: 1.4rem;
    font-weight: 700;
    letter-spacing: 0.07rem;
    line-height: 1.5;
    text-transform: uppercase;
}

.key-data-summary-empty {
    margin: 0;
    color: var(--p-text-muted-color);
    font-size: 1.3rem;
}

.key-data-summary-rows {
    display: flex;
    flex-direction: column;
    margin: 0;
}

.key-data-summary-row {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 1.2rem;
    padding-block: 0.7rem;
    border-block-end: 0.1rem dashed var(--p-content-border-color);
    font-size: 1.3rem;
}

.key-data-summary-row:last-child {
    border-block-end: none;
}

.key-data-summary-row .p-button {
    --p-button-label-font-weight: 500;
    padding: 0;
    border: none;
    color: var(--p-text-muted-color);
    font-size: 1.3rem;
    text-align: start;
}

.key-data-summary-row .p-button:not(:disabled):hover {
    color: var(--p-primary-color);
}

.key-data-summary-row dd {
    margin: 0;
    font-weight: 600;
    text-align: end;
}
</style>
