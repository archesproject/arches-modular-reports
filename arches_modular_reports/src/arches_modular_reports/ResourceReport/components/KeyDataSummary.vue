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
    gap: 1.2rem;
    padding: 1.6rem;
    border: 0.1rem solid var(--p-content-border-color);
    border-radius: var(--p-content-border-radius);
    background: var(--p-content-background);
}

.key-data-summary-title {
    margin: 0;
    color: var(--p-text-muted-color);
    font-size: 1.2rem;
    font-weight: 700;
    letter-spacing: 0.08rem;
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
    gap: 0.8rem;
    margin: 0;
}

.key-data-summary-row {
    display: flex;
    align-items: baseline;
    gap: 0.8rem;
    font-size: 1.3rem;
}

.key-data-summary-row dd {
    margin: 0;
}
</style>
