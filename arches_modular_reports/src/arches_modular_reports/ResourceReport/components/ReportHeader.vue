<script setup lang="ts">
import { computed } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";
import Tag from "openvue/tag";

import { buildExportUrl } from "@/arches_modular_reports/ResourceReport/api.ts";
import {
    DEFAULT_GRAPH_ICON_CLASS,
    EMPTY_VALUE,
} from "@/arches_modular_reports/ResourceReport/constants.ts";
import { lifecycleSeverity } from "@/arches_modular_reports/ResourceReport/utils/lifecycle-severity.ts";
import { summaryRows } from "@/arches_modular_reports/ResourceReport/utils/summary-rows.ts";

import type {
    ExportFormat,
    HeaderConfig,
    LifecycleStateSummary,
    ReportData,
    TagSeverity,
} from "@/arches_modular_reports/ResourceReport/types.ts";

const TRANSITION_LIFECYCLE = "transition-lifecycle" as const;

const { reportData, headerConfig, isTransitioning } = defineProps<{
    reportData: ReportData;
    headerConfig: HeaderConfig;
    isTransitioning: boolean;
}>();

const emit = defineEmits<{
    (event: typeof TRANSITION_LIFECYCLE, lifecycleStateId: string): void;
}>();

const { $gettext } = useGettext();

const exportFormatLabels: Record<ExportFormat, string> = {
    "json-ld": $gettext("JSON-LD"),
    json: $gettext("JSON"),
    csv: $gettext("CSV"),
};

const currentLifecycleState = computed(
    () => reportData.context.lifecycle_state,
);

const displayName = computed(() => {
    const resourceName = reportData.resource.name?.trim();
    if (resourceName) {
        return resourceName;
    }
    return $gettext(
        "New %{graphName}",
        {
            graphName: reportData.context.graph.name,
        },
        true,
    );
});

const graphIconClass = computed(() => {
    if (reportData.context.graph.iconclass) {
        return reportData.context.graph.iconclass;
    }
    return DEFAULT_GRAPH_ICON_CLASS;
});

const lifecycleTagSeverity = computed(() =>
    lifecycleSeverity(
        currentLifecycleState.value,
        headerConfig.lifecycle_severities,
    ),
);

const previousStates = computed(
    () =>
        currentLifecycleState.value.previous_resource_instance_lifecycle_states,
);

const nextStates = computed(
    () => currentLifecycleState.value.next_resource_instance_lifecycle_states,
);

const hasTransitions = computed(
    () =>
        reportData.context.permissions.is_reviewer &&
        (previousStates.value.length > 0 || nextStates.value.length > 0),
);

const summaryLines = computed(() =>
    summaryRows(
        headerConfig.summary,
        reportData.resource.aliased_data,
        reportData.context.language,
    ),
);

const isHoldingTransitions = computed(
    () =>
        reportData.changeSet.pendingChanges.value.length > 0 ||
        reportData.changeSet.isSaving.value,
);

function transitionSeverity(
    lifecycleState: LifecycleStateSummary,
): TagSeverity {
    if (lifecycleState.can_edit_resource_instances) {
        return "info";
    }
    return "danger";
}

function exportAriaLabel(exportFormat: ExportFormat): string {
    return $gettext(
        "Export as %{exportFormat}",
        {
            exportFormat: exportFormatLabels[exportFormat],
        },
        true,
    );
}
</script>

<template>
    <header class="report-header">
        <div class="report-header-thumb">
            <i
                aria-hidden="true"
                :class="graphIconClass"
            />
        </div>
        <div class="report-header-content">
            <div class="report-header-title">
                <h2 class="report-header-name">{{ displayName }}</h2>
                <Tag
                    :value="currentLifecycleState.name"
                    :severity="lifecycleTagSeverity"
                    :rounded="true"
                />
            </div>
            <span class="report-header-type">{{
                reportData.context.graph.name
            }}</span>
            <dl
                v-if="summaryLines.length > 0"
                class="report-header-summary"
            >
                <div
                    v-for="summaryLine in summaryLines"
                    :key="summaryLine.nodeAlias"
                    class="report-header-summary-line"
                >
                    <dt>{{ summaryLine.label }}</dt>
                    <dd>{{ summaryLine.values[0] ?? EMPTY_VALUE }}</dd>
                </div>
            </dl>
        </div>
        <div
            v-if="hasTransitions || headerConfig.export_formats.length > 0"
            class="report-header-actions"
        >
            <div
                v-if="hasTransitions"
                class="report-header-lifecycle-actions"
            >
                <Button
                    v-for="lifecycleState in previousStates"
                    :key="lifecycleState.id"
                    icon="pi pi-arrow-left"
                    size="small"
                    :label="lifecycleState.action_label"
                    :severity="transitionSeverity(lifecycleState)"
                    :loading="isTransitioning"
                    :disabled="isHoldingTransitions"
                    @click="emit(TRANSITION_LIFECYCLE, lifecycleState.id)"
                />
                <Button
                    v-for="lifecycleState in nextStates"
                    :key="lifecycleState.id"
                    icon="pi pi-arrow-right"
                    icon-pos="right"
                    size="small"
                    :label="lifecycleState.action_label"
                    :severity="transitionSeverity(lifecycleState)"
                    :loading="isTransitioning"
                    :disabled="isHoldingTransitions"
                    @click="emit(TRANSITION_LIFECYCLE, lifecycleState.id)"
                />
            </div>
            <nav
                v-if="headerConfig.export_formats.length > 0"
                class="report-header-exports"
                :aria-label="$gettext('Export')"
            >
                <Button
                    v-for="exportFormat in headerConfig.export_formats"
                    :key="exportFormat"
                    as="a"
                    variant="link"
                    size="small"
                    target="_blank"
                    rel="noopener"
                    :href="
                        buildExportUrl(
                            reportData.resource.resourceinstanceid,
                            exportFormat,
                        )
                    "
                    :label="exportFormatLabels[exportFormat]"
                    :aria-label="exportAriaLabel(exportFormat)"
                />
            </nav>
        </div>
    </header>
</template>

<style scoped>
.report-header {
    display: flex;
    align-items: stretch;
    min-block-size: 9rem;
    border-block-end: 0.1rem solid var(--p-content-border-color);
    background: var(--p-content-background);
}

.report-header-thumb {
    display: flex;
    flex-shrink: 0;
    align-items: center;
    justify-content: center;
    min-inline-size: 9rem;
    padding-inline: 2.4rem;
    background: var(--p-highlight-background);
    color: var(--p-highlight-color);
    font-size: 2.4rem;
}

.report-header-content {
    display: flex;
    flex: 1;
    flex-direction: column;
    justify-content: center;
    gap: 0.2rem;
    min-inline-size: 0;
    padding-block: 1.2rem;
    padding-inline: 1.6rem;
}

.report-header-title {
    display: flex;
    align-items: center;
    gap: 1rem;
    min-inline-size: 0;
}

.report-header-name {
    margin: 0;
    overflow: hidden;
    color: var(--p-text-color);
    font-size: 1.6rem;
    font-weight: 700;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.report-header-actions {
    display: grid;
    flex-shrink: 0;
    grid-template-rows: 1fr auto;
    justify-items: end;
    gap: 0.8rem;
    padding-block: 1.2rem;
    padding-inline: 1.6rem;
}

.report-header-lifecycle-actions {
    display: flex;
    align-self: start;
    gap: 0.8rem;
}

.report-header-type {
    color: var(--p-text-muted-color);
    font-size: 1.2rem;
}

.report-header-summary {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
    margin: 0;
    color: var(--p-text-muted-color);
    font-size: 1.2rem;
}

.report-header-summary-line {
    display: flex;
    gap: 0.5rem;
}

.report-header-summary dt {
    font-weight: 600;
}

.report-header-summary dd {
    margin: 0;
}

.report-header-exports {
    display: flex;
    grid-row: 2;
    gap: 0.4rem;
}
</style>
