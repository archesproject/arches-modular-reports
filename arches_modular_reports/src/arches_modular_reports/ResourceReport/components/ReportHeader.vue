<script setup lang="ts">
import { computed } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";
import Tag from "openvue/tag";

import { buildExportUrl } from "@/arches_modular_reports/ResourceReport/api.ts";
import { EXPORT_FORMAT_LABELS } from "@/arches_modular_reports/ResourceReport/constants.ts";

import type {
    ExportFormat,
    LifecycleStateSummary,
    SummaryLine,
    TagSeverity,
} from "@/arches_modular_reports/ResourceReport/types.ts";

const TRANSITION_LIFECYCLE = "transition-lifecycle" as const;

const {
    displayName,
    graphName,
    graphIconClass,
    lifecycleStateName,
    lifecycleSeverity,
    previousStates,
    nextStates,
    isTransitioning,
    summaryLines,
    exportFormats,
    resourceInstanceId,
} = defineProps<{
    displayName: string;
    graphName: string;
    graphIconClass: string;
    lifecycleStateName: string;
    lifecycleSeverity: TagSeverity;
    previousStates: LifecycleStateSummary[];
    nextStates: LifecycleStateSummary[];
    isTransitioning: boolean;
    summaryLines: SummaryLine[];
    exportFormats: ExportFormat[];
    resourceInstanceId: string;
}>();

const emit = defineEmits<{
    (event: typeof TRANSITION_LIFECYCLE, lifecycleStateId: string): void;
}>();

const { $gettext } = useGettext();

const hasTransitions = computed(
    () => previousStates.length > 0 || nextStates.length > 0,
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
    return $gettext("Export as %{exportFormat}", {
        exportFormat: EXPORT_FORMAT_LABELS[exportFormat],
    });
}
</script>

<template>
    <header class="report-header">
        <div class="report-header-thumb">
            <i
                :class="graphIconClass"
                aria-hidden="true"
            />
        </div>
        <div class="report-header-content">
            <div class="report-header-name-row">
                <h2 class="report-header-name">{{ displayName }}</h2>
                <Tag
                    :value="lifecycleStateName"
                    :severity="lifecycleSeverity"
                    :rounded="true"
                />
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
                        @click="emit(TRANSITION_LIFECYCLE, lifecycleState.id)"
                    />
                </div>
            </div>
            <span class="report-header-type">{{ graphName }}</span>
            <dl
                v-if="summaryLines.length > 0"
                class="report-header-summary"
            >
                <div
                    v-for="summaryLine in summaryLines"
                    :key="summaryLine.label"
                    class="report-header-summary-line"
                >
                    <dt>{{ summaryLine.label }}</dt>
                    <dd>{{ summaryLine.value }}</dd>
                </div>
            </dl>
        </div>
        <nav
            v-if="exportFormats.length > 0"
            class="report-header-exports"
            :aria-label="$gettext('Export')"
        >
            <Button
                v-for="exportFormat in exportFormats"
                :key="exportFormat"
                as="a"
                variant="link"
                size="small"
                target="_blank"
                rel="noopener"
                :href="buildExportUrl(resourceInstanceId, exportFormat)"
                :label="EXPORT_FORMAT_LABELS[exportFormat]"
                :aria-label="exportAriaLabel(exportFormat)"
            />
        </nav>
    </header>
</template>

<style scoped>
.report-header {
    display: flex;
    align-items: stretch;
    min-height: 9rem;
    border-block-end: 0.1rem solid var(--p-content-border-color);
    background: var(--p-content-background);
}

.report-header-thumb {
    display: flex;
    flex-shrink: 0;
    align-items: center;
    justify-content: center;
    min-width: 9rem;
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
    min-width: 0;
    padding-block: 1.2rem;
    padding-inline: 1.6rem;
}

.report-header-name-row {
    display: flex;
    align-items: center;
    gap: 1rem;
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

.report-header-lifecycle-actions {
    display: flex;
    flex-shrink: 0;
    gap: 0.8rem;
    margin-inline-start: auto;
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
    align-items: flex-end;
    gap: 0.4rem;
    padding-block: 1.2rem;
    padding-inline: 1.6rem;
}
</style>
