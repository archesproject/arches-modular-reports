<script setup lang="ts">
import { computed } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";
import Message from "openvue/message";
import Tag from "openvue/tag";

import { useReportData } from "@/arches_modular_reports/ResourceReport/composables/useReportData.ts";
import {
    DEFAULT_GRAPH_ICON_CLASS,
    EMPTY_VALUE,
} from "@/arches_modular_reports/ResourceReport/constants.ts";
import { lifecycleSeverity } from "@/arches_modular_reports/ResourceReport/utils/lifecycle-severity.ts";
import { summaryRows } from "@/arches_modular_reports/ResourceReport/utils/summary-rows.ts";

import type {
    ComponentNode,
    LifecycleStateSummary,
    ReportHeaderConfig,
    TagSeverity,
} from "@/arches_modular_reports/ResourceReport/types.ts";

const { component } = defineProps<{
    component: ComponentNode<ReportHeaderConfig>;
}>();

const { $gettext } = useGettext();
const reportData = useReportData();

const currentLifecycleState = computed(
    () => reportData.value.context.lifecycle_state,
);

const displayName = computed(() => {
    const resourceName = reportData.value.resource.name?.trim();
    if (resourceName) {
        return resourceName;
    }
    return $gettext(
        "New %{graphName}",
        {
            graphName: reportData.value.context.graph.name,
        },
        true,
    );
});

const graphIconClass = computed(() => {
    if (reportData.value.context.graph.iconclass) {
        return reportData.value.context.graph.iconclass;
    }
    return DEFAULT_GRAPH_ICON_CLASS;
});

// The model's search colour, so the report's thumb matches its search card.
const thumbAccentStyle = computed(() => ({
    "--report-header-accent-color":
        reportData.value.context.graph.color || "var(--p-primary-color)",
}));

const lifecycleTagSeverity = computed(() =>
    lifecycleSeverity(currentLifecycleState.value),
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
        reportData.value.context.permissions.is_reviewer &&
        (previousStates.value.length > 0 || nextStates.value.length > 0),
);

const summaryLines = computed(() =>
    summaryRows(
        component.config.summary ?? [],
        reportData.value.resource.aliased_data,
        reportData.value.context.language,
    ),
);

const isHoldingTransitions = computed(
    () =>
        reportData.value.changeSet.pendingChanges.value.length > 0 ||
        reportData.value.changeSet.isSaving.value,
);

function transitionSeverity(
    lifecycleState: LifecycleStateSummary,
): TagSeverity {
    if (lifecycleState.can_edit_resource_instances) {
        return "info";
    }
    return "danger";
}
</script>

<template>
    <header class="report-header">
        <div
            class="report-header-thumb"
            :style="thumbAccentStyle"
        >
            <i
                aria-hidden="true"
                class="report-header-icon"
                :class="graphIconClass"
            />
            <span class="report-header-type">{{
                reportData.context.graph.name
            }}</span>
        </div>
        <div class="report-header-content">
            <div class="report-header-title">
                <h2 class="report-header-name">{{ displayName }}</h2>
                <Tag
                    class="report-header-state"
                    :value="currentLifecycleState.name"
                    :severity="lifecycleTagSeverity"
                    :rounded="true"
                />
            </div>
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
        <div class="report-header-actions">
            <div
                v-if="hasTransitions"
                class="report-header-lifecycle-actions"
            >
                <Button
                    v-for="lifecycleState in previousStates"
                    :key="lifecycleState.id"
                    class="report-header-transition"
                    icon="pi pi-arrow-left"
                    size="small"
                    :label="lifecycleState.action_label"
                    :severity="transitionSeverity(lifecycleState)"
                    :loading="reportData.lifecycle.isTransitioning"
                    :disabled="isHoldingTransitions"
                    @click="reportData.lifecycle.transition(lifecycleState.id)"
                />
                <Button
                    v-for="lifecycleState in nextStates"
                    :key="lifecycleState.id"
                    class="report-header-transition"
                    icon="pi pi-arrow-right"
                    icon-pos="right"
                    size="small"
                    :label="lifecycleState.action_label"
                    :severity="transitionSeverity(lifecycleState)"
                    :loading="reportData.lifecycle.isTransitioning"
                    :disabled="isHoldingTransitions"
                    @click="reportData.lifecycle.transition(lifecycleState.id)"
                />
            </div>
        </div>
    </header>
    <Message
        v-if="reportData.lifecycle.transitionError"
        severity="error"
    >
        <span>
            {{
                $gettext(
                    "Unable to change the lifecycle state: %{message}",
                    {
                        message: reportData.lifecycle.transitionError.message,
                    },
                    true,
                )
            }}
        </span>
    </Message>
</template>

<style scoped>
.report-header {
    display: flex;
    align-items: stretch;
    min-block-size: 9rem;
    border-block-end: 0.1rem solid var(--p-content-border-color);
    background: var(--p-content-background);
}

/* Icon over model name, following the arches-search result card thumb. */
/*
 * The background tints the model colour as search does. Model colours are
 * often translucent and pale, so the icon and label drop the alpha and mix
 * toward the text colour: 40% keeps every rascoll model at 4.5:1 or better
 * in both colour schemes, and the larger icon keeps 60% at 3:1 or better.
 */
.report-header-thumb {
    --report-header-accent-opaque: rgb(
        from var(--report-header-accent-color) r g b
    );
    display: flex;
    flex-direction: column;
    flex-shrink: 0;
    align-items: center;
    justify-content: center;
    gap: 0.4rem;
    inline-size: 11rem;
    padding-block: 1.2rem;
    padding-inline: 0.6rem;
    background: color-mix(
        in srgb,
        var(--report-header-accent-color) 12%,
        var(--p-content-background)
    );
    color: color-mix(
        in srgb,
        var(--report-header-accent-opaque) 40%,
        var(--p-text-color)
    );
    text-align: center;
}

.report-header-icon {
    color: color-mix(
        in srgb,
        var(--report-header-accent-opaque) 60%,
        var(--p-text-color)
    );
    font-size: 2.4rem;
}

.report-header-content {
    display: flex;
    flex: 1;
    flex-direction: column;
    justify-content: center;
    gap: 0.2rem;
    min-inline-size: 0;
    line-height: 1.2;
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
    font-size: 1.8rem;
    font-weight: 600;
    line-height: 1.2;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.report-header-actions {
    display: flex;
    flex-shrink: 0;
    align-items: flex-start;
    padding-block: 1.2rem;
    padding-inline: 1.6rem;
}

.report-header-lifecycle-actions {
    display: flex;
    align-self: start;
    gap: 0.8rem;
    padding-block: 1.75rem;
}

.report-header-title .report-header-state {
    gap: 0.4rem;
    padding-block: 0.3rem;
    padding-inline: 1.25rem;
    border: 0.1rem solid var(--p-blue-200);
    border-radius: 2rem;
    background: var(--p-blue-50);
    color: var(--p-blue-700);
    font-size: 1.25rem;
    font-weight: 600;
}

.report-header-title .report-header-state.p-tag-success {
    border-color: var(--p-green-200);
    background: var(--p-green-50);
    color: var(--p-green-800);
}

.report-header-title .report-header-state.p-tag-danger {
    border-color: var(--p-red-200);
    background: var(--resource-report-deleted-background);
    color: var(--resource-report-deleted-color);
}

.report-header-lifecycle-actions .report-header-transition {
    --p-button-label-font-weight: 400;
    gap: 0.7rem;
    padding-block: 0.6rem;
    padding-inline: 1.2rem;
    border-color: var(--p-sky-600);
    border-radius: 0.2rem;
    background: var(--p-sky-600);
    color: var(--p-surface-0);
    font-size: 1.3rem;
    line-height: 1.2;
}

.report-header-lifecycle-actions
    .report-header-transition:not(:disabled):hover {
    border-color: var(--p-sky-700);
    background: var(--p-sky-700);
    color: var(--p-surface-0);
}

.report-header-lifecycle-actions .report-header-transition.p-button-danger {
    border-color: var(--p-red-600);
    background: var(--p-red-600);
}

.report-header-lifecycle-actions
    .report-header-transition.p-button-danger:not(:disabled):hover {
    border-color: var(--p-red-700);
    background: var(--p-red-700);
}

.report-header-type {
    font-size: 0.9rem;
    font-weight: 600;
    letter-spacing: 0.036rem;
    line-height: 1.3;
    text-transform: uppercase;
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
    font-weight: 400;
}

.report-header-summary dd {
    margin: 0;
    font-weight: 600;
}
</style>
