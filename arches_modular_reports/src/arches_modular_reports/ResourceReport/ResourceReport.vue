<script setup lang="ts">
import { computed, inject, onMounted, onUnmounted, ref } from "vue";
import { useGettext } from "vue3-gettext";

import Message from "openvue/message";
import Skeleton from "openvue/skeleton";

import DataWorkspace from "@/arches_modular_reports/ResourceReport/components/DataWorkspace/DataWorkspace.vue";
import EditListTray from "@/arches_modular_reports/ResourceReport/components/EditListTray.vue";
import GraphWorkspace from "@/arches_modular_reports/ResourceReport/components/GraphWorkspace.vue";
import ReportHeader from "@/arches_modular_reports/ResourceReport/components/ReportHeader.vue";
import ReportWorkspace from "@/arches_modular_reports/ResourceReport/components/ReportWorkspace/ReportWorkspace.vue";
import WorkspaceStrip from "@/arches_modular_reports/ResourceReport/components/WorkspaceStrip.vue";

import { loadComponent } from "@/arches_modular_reports/ModularReport/utils.ts";
import { useGraphWidgetConfigs } from "@/arches_modular_reports/ResourceReport/composables/useGraphWidgetConfigs.ts";
import { useReportContext } from "@/arches_modular_reports/ResourceReport/composables/useReportContext.ts";
import { useResourceChangeSet } from "@/arches_modular_reports/ResourceReport/composables/useResourceChangeSet.ts";
import { useReportWorkspaces } from "@/arches_modular_reports/ResourceReport/composables/useReportWorkspaces.ts";
import {
    DATA_WORKSPACE,
    EMPTY_VALUE,
    GRAPH_WORKSPACE,
    REPORT_WORKSPACE,
} from "@/arches_modular_reports/ResourceReport/constants.ts";
import { findNodeValues } from "@/arches_modular_reports/ResourceReport/utils/find-node-values.ts";
import { folioLocations } from "@/arches_modular_reports/ResourceReport/utils/folio-locations.ts";
import { indexGraphNodes } from "@/arches_modular_reports/ResourceReport/utils/graph-nodes.ts";
import { lifecycleSeverity } from "@/arches_modular_reports/ResourceReport/utils/lifecycle-severity.ts";
import { localizeLabel } from "@/arches_modular_reports/ResourceReport/utils/localize-label.ts";

import type { Component } from "vue";
import type {
    EditTileRequest,
    ReportData,
    ResourceReportConfig,
    SummaryLine,
} from "@/arches_modular_reports/ResourceReport/types.ts";

const BUILT_IN_WORKSPACE_COMPONENTS: Record<string, Component> = {
    [REPORT_WORKSPACE]: ReportWorkspace,
    [DATA_WORKSPACE]: DataWorkspace,
    [GRAPH_WORKSPACE]: GraphWorkspace,
};
const DEFAULT_GRAPH_ICON_CLASS = "pi pi-database";

const { component, resourceInstanceId } = defineProps<{
    component: { component: string; config: ResourceReportConfig };
    resourceInstanceId: string;
}>();

const graphSlug = inject<string>("graphSlug", "");

const { $gettext } = useGettext();
const reportContext = useReportContext(resourceInstanceId);
const graphWidgetConfigs = useGraphWidgetConfigs(graphSlug);
const changeSet = useResourceChangeSet(graphSlug, resourceInstanceId);
const { context, isTransitioning, transitionError, transitionLifecycle } =
    reportContext;
const { workspaces, activeWorkspace, selectWorkspace } = useReportWorkspaces(
    () => component.config.workspaces ?? [],
    () => canEdit.value,
    () => context.value?.language ?? "",
);

const editorTarget = ref<EditTileRequest | null>(null);

const fetchError = computed(
    () =>
        reportContext.fetchError.value ??
        graphWidgetConfigs.fetchError.value ??
        changeSet.fetchError.value,
);

const canEdit = computed(
    () =>
        context.value?.permissions.can_edit === true &&
        context.value.lifecycle_state.can_edit_resource_instances,
);

const hasPendingChanges = computed(
    () => changeSet.pendingChanges.value.length > 0,
);

const reportData = computed<ReportData | null>(() => {
    if (
        context.value === null ||
        graphWidgetConfigs.nodegroupWidgetConfigs.value === null ||
        changeSet.workingResource.value === null
    ) {
        return null;
    }
    return {
        context: context.value,
        nodegroupWidgetConfigs: graphWidgetConfigs.nodegroupWidgetConfigs.value,
        graphNodesByAlias: indexGraphNodes(
            graphWidgetConfigs.nodegroupWidgetConfigs.value,
        ),
        folioLocations: folioLocations(
            component.config.workspaces ?? [],
            context.value.language,
        ),
        resource: changeSet.workingResource.value,
        canEdit: canEdit.value,
        changeSet,
        editor: {
            target: editorTarget.value,
            open: openEditor,
            close: closeEditor,
        },
    };
});

const graphName = computed(() => context.value?.graph.name ?? "");

const graphIconClass = computed(
    () => context.value?.graph.iconclass ?? DEFAULT_GRAPH_ICON_CLASS,
);

const exportFormats = computed(
    () => component.config.header?.export_formats ?? [],
);

const displayName = computed(() => {
    const resourceName = changeSet.workingResource.value?.name?.trim();
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
    if (reportData.value === null) {
        return [];
    }
    const { graphNodesByAlias, resource } = reportData.value;
    const activeLanguage = reportData.value.context.language;
    return (component.config.header?.summary ?? []).map((summaryEntry) => ({
        label:
            localizeLabel(summaryEntry.label, activeLanguage) ??
            graphNodesByAlias[summaryEntry.node_alias].label,
        value:
            findNodeValues(resource.aliased_data, summaryEntry.node_alias)[0]
                ?.display_value || EMPTY_VALUE,
    }));
});

const activeWorkspaceComponent = computed(() => {
    if (activeWorkspace.value === undefined) {
        return null;
    }
    const componentName = activeWorkspace.value.component;
    return (
        BUILT_IN_WORKSPACE_COMPONENTS[componentName] ??
        loadComponent(componentName)
    );
});

onMounted(() => {
    window.addEventListener("beforeunload", warnAboutPendingChanges);
});

onUnmounted(() => {
    window.removeEventListener("beforeunload", warnAboutPendingChanges);
});

function openEditor(editTileRequest: EditTileRequest): void {
    editorTarget.value = editTileRequest;
}

function closeEditor(): void {
    editorTarget.value = null;
}

function warnAboutPendingChanges(event: BeforeUnloadEvent): void {
    if (hasPendingChanges.value) {
        event.preventDefault();
    }
}
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
        v-else-if="reportData && workspaces.length === 0"
        severity="error"
    >
        <span>
            {{ $gettext("This report configuration has no workspaces.") }}
        </span>
    </Message>
    <div
        v-else-if="reportData && activeWorkspace && lifecycleState"
        class="resource-report"
        :dir="context?.language_dir"
    >
        <WorkspaceStrip
            v-if="workspaces.length > 1"
            :workspaces="workspaces"
            :active-workspace-id="activeWorkspace.id"
            @select-workspace="selectWorkspace"
        />
        <p
            v-if="activeWorkspace.description"
            class="resource-report-caption"
        >
            {{ activeWorkspace.description }}
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
        <Message
            v-if="changeSet.addError.value"
            severity="error"
        >
            <span>{{ changeSet.addError.value.message }}</span>
        </Message>
        <component
            :is="activeWorkspaceComponent"
            class="resource-report-workspace"
            :workspace-config="activeWorkspace.config"
            :report-data="reportData"
        />
        <EditListTray
            v-if="reportData.canEdit && hasPendingChanges"
            :report-data="reportData"
        />
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

.resource-report-workspace {
    flex: 1;
    min-height: 0;
}

.resource-report-loading {
    display: flex;
    flex-direction: column;
    gap: 1.6rem;
    padding: 1.6rem;
}
</style>
