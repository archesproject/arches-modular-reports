<script setup lang="ts">
import { computed, inject } from "vue";
import { useGettext } from "vue3-gettext";

import Message from "openvue/message";
import Skeleton from "openvue/skeleton";
import Splitter from "openvue/splitter";
import SplitterPanel from "openvue/splitterpanel";

import DataView from "@/arches_modular_reports/ResourceReport/components/DataView.vue";
import GraphView from "@/arches_modular_reports/ResourceReport/components/GraphView.vue";
import ReportHeader from "@/arches_modular_reports/ResourceReport/components/ReportHeader.vue";
import ReportPlaceholder from "@/arches_modular_reports/ResourceReport/components/ReportPlaceholder.vue";
import ReportView from "@/arches_modular_reports/ResourceReport/components/ReportView.vue";
import ViewStrip from "@/arches_modular_reports/ResourceReport/components/ViewStrip.vue";

import { loadComponent } from "@/arches_modular_reports/ModularReport/utils.ts";
import { useReportContext } from "@/arches_modular_reports/ResourceReport/composables/useReportContext.ts";
import { useReportSchema } from "@/arches_modular_reports/ResourceReport/composables/useReportSchema.ts";
import { useReportViews } from "@/arches_modular_reports/ResourceReport/composables/useReportViews.ts";
import { useResourceData } from "@/arches_modular_reports/ResourceReport/composables/useResourceData.ts";
import {
    DATA_VIEW,
    EMPTY_VALUE,
    GRAPH_VIEW,
    REPORT_VIEW,
} from "@/arches_modular_reports/ResourceReport/constants.ts";
import { findNodeValues } from "@/arches_modular_reports/ResourceReport/utils/find-node-values.ts";
import { lifecycleSeverity } from "@/arches_modular_reports/ResourceReport/utils/lifecycle-severity.ts";
import { localizeLabel } from "@/arches_modular_reports/ResourceReport/utils/localize-label.ts";

import type { Component } from "vue";
import type {
    ResourceReportConfig,
    SummaryLine,
} from "@/arches_modular_reports/ResourceReport/types.ts";

const BUILT_IN_VIEW_COMPONENTS: Record<string, Component> = {
    [REPORT_VIEW]: ReportView,
    [DATA_VIEW]: DataView,
    [GRAPH_VIEW]: GraphView,
};
const DEFAULT_GRAPH_ICON_CLASS = "pi pi-database";
const REPORT_PANE_SIZES = { main: 60, aside: 40 };
const DATA_PANE_SIZES = { main: 40, aside: 60 };
const MINIMUM_PANE_SIZE = 20;
const SPLITTER_STATE_KEY_PREFIX = "arches-modular-reports-resource-report-";

const { component, resourceInstanceId } = defineProps<{
    component: { component: string; config: ResourceReportConfig };
    resourceInstanceId: string;
}>();

const graphSlug = inject<string>("graphSlug", "");

const { $gettext } = useGettext();
const reportContext = useReportContext(resourceInstanceId);
const reportSchema = useReportSchema(resourceInstanceId);
const resourceData = useResourceData(graphSlug, resourceInstanceId);
const { context, isTransitioning, transitionError, transitionLifecycle } =
    reportContext;
const { views, activeView, selectView } = useReportViews(
    () => component.config.views ?? [],
    () => context.value?.permissions.can_edit === true,
    () => context.value?.language ?? "",
);

const fetchError = computed(
    () =>
        reportContext.fetchError.value ??
        reportSchema.fetchError.value ??
        resourceData.fetchError.value,
);

const isLoaded = computed(
    () =>
        context.value !== null &&
        reportSchema.schema.value !== null &&
        resourceData.resource.value !== null,
);

const graphName = computed(() => context.value?.graph.name ?? "");

const graphIconClass = computed(
    () => context.value?.graph.iconclass ?? DEFAULT_GRAPH_ICON_CLASS,
);

const exportFormats = computed(
    () => component.config.header?.export_formats ?? [],
);

const displayName = computed(() => {
    const resourceName = resourceData.resource.value?.name?.trim();
    if (resourceName) {
        return resourceName;
    }
    return $gettext("New %{graphName}", { graphName: graphName.value });
});

const lifecycleState = computed(() => context.value?.lifecycle_state);

const currentLifecycleSeverity = computed(() => {
    if (!lifecycleState.value) {
        return "secondary";
    }
    return lifecycleSeverity(
        lifecycleState.value,
        component.config.header?.lifecycle_severities,
    );
});

const canTransitionLifecycle = computed(
    () => context.value?.permissions.is_reviewer === true,
);

const transitionErrorMessage = computed(() => {
    if (!transitionError.value) {
        return "";
    }
    return $gettext("Unable to change the lifecycle state: %{message}", {
        message: transitionError.value.message,
    });
});

const previousLifecycleStates = computed(() => {
    if (!canTransitionLifecycle.value || !lifecycleState.value) {
        return [];
    }
    return lifecycleState.value.previous_resource_instance_lifecycle_states;
});

const nextLifecycleStates = computed(() => {
    if (!canTransitionLifecycle.value || !lifecycleState.value) {
        return [];
    }
    return lifecycleState.value.next_resource_instance_lifecycle_states;
});

const summaryLines = computed<SummaryLine[]>(() => {
    const resource = resourceData.resource.value;
    const schema = reportSchema.schema.value;
    const activeLanguage = context.value?.language ?? "";
    if (resource === null || schema === null) {
        return [];
    }
    return (component.config.header?.summary ?? []).map((summaryEntry) => ({
        label:
            localizeLabel(summaryEntry.label, activeLanguage) ??
            schema.nodesByAlias[summaryEntry.node_alias].widget_label,
        value:
            findNodeValues(resource.aliased_data, summaryEntry.node_alias)[0]
                ?.display_value || EMPTY_VALUE,
    }));
});

const paneSizes = computed(() => {
    if (activeView.value?.layout === "data") {
        return DATA_PANE_SIZES;
    }
    return REPORT_PANE_SIZES;
});

const activeViewComponent = computed(() => {
    const componentName = activeView.value?.component ?? REPORT_VIEW;
    return (
        BUILT_IN_VIEW_COMPONENTS[componentName] ?? loadComponent(componentName)
    );
});
</script>

<template>
    <Message
        v-if="fetchError"
        severity="error"
    >
        <span>
            {{
                $gettext("Unable to load this report: %{message}", {
                    message: fetchError.message,
                })
            }}
        </span>
    </Message>
    <Message
        v-else-if="isLoaded && views.length === 0"
        severity="error"
    >
        <span>{{ $gettext("This report configuration has no views.") }}</span>
    </Message>
    <div
        v-else-if="isLoaded && activeView && lifecycleState"
        class="resource-report"
        :dir="context?.language_dir"
    >
        <ViewStrip
            v-if="views.length > 1"
            :views="views"
            :active-view-id="activeView.id"
            @select-view="selectView"
        />
        <p
            v-if="activeView.description"
            class="resource-report-caption"
        >
            {{ activeView.description }}
        </p>
        <ReportHeader
            :display-name="displayName"
            :graph-name="graphName"
            :graph-icon-class="graphIconClass"
            :lifecycle-state-name="lifecycleState.name"
            :lifecycle-severity="currentLifecycleSeverity"
            :previous-states="previousLifecycleStates"
            :next-states="nextLifecycleStates"
            :is-transitioning="isTransitioning"
            :summary-lines="summaryLines"
            :export-formats="exportFormats"
            :resource-instance-id="resourceInstanceId"
            @transition-lifecycle="transitionLifecycle"
        />
        <Message
            v-if="transitionError"
            severity="error"
        >
            <span>{{ transitionErrorMessage }}</span>
        </Message>
        <Splitter
            v-if="activeView.layout !== 'full'"
            :key="activeView.layout"
            class="resource-report-splitter"
            state-storage="local"
            :state-key="`${SPLITTER_STATE_KEY_PREFIX}${activeView.layout}`"
        >
            <SplitterPanel
                class="resource-report-pane"
                :size="paneSizes.main"
                :min-size="MINIMUM_PANE_SIZE"
            >
                <component :is="activeViewComponent" />
            </SplitterPanel>
            <SplitterPanel
                class="resource-report-pane resource-report-aside"
                :size="paneSizes.aside"
                :min-size="MINIMUM_PANE_SIZE"
            >
                <ReportPlaceholder
                    v-if="activeView.layout === 'data'"
                    icon="pi pi-pencil"
                    :message="
                        $gettext(
                            'Select a branch from the browser to begin editing.',
                        )
                    "
                />
                <ReportPlaceholder
                    v-else
                    icon="pi pi-list"
                    :message="
                        $gettext('The key data summary is not available yet.')
                    "
                />
            </SplitterPanel>
        </Splitter>
        <div
            v-else
            class="resource-report-pane resource-report-full-pane"
        >
            <component :is="activeViewComponent" />
        </div>
    </div>
    <div
        v-else
        class="resource-report-loading"
    >
        <Skeleton height="9rem" />
        <Skeleton height="24rem" />
    </div>
</template>

<style scoped>
.resource-report {
    display: flex;
    flex-direction: column;
    height: 100%;
    background: var(--p-content-background);
}

.resource-report-caption {
    margin: 0;
    padding-block: 0.5rem;
    padding-inline: 1.6rem;
    border-block-end: 0.1rem solid var(--p-content-border-color);
    background: var(
        --p-resource-report-caption-background,
        var(--p-content-hover-background)
    );
    color: var(--p-text-muted-color);
    font-size: 1.15rem;
}

.resource-report-splitter {
    flex: 1;
    min-height: 0;
    border: none;
    border-radius: 0;
}

.resource-report-pane {
    display: flex;
    flex-direction: column;
    min-width: 0;
    overflow-y: auto;
}

.resource-report-full-pane {
    flex: 1;
    min-height: 0;
}

.resource-report-aside {
    background: var(
        --p-resource-report-aside-background,
        var(--p-content-hover-background)
    );
}

.resource-report-loading {
    display: flex;
    flex-direction: column;
    gap: 1.6rem;
    padding: 1.6rem;
}
</style>
