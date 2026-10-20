<script setup lang="ts">
import { computed, inject, onMounted, onUnmounted, ref, watch } from "vue";
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
import {
    DATA_WORKSPACE,
    GRAPH_WORKSPACE,
    REPORT_WORKSPACE,
} from "@/arches_modular_reports/ResourceReport/constants.ts";
import { folioLocations } from "@/arches_modular_reports/ResourceReport/utils/folio-locations.ts";
import { indexGraphNodes } from "@/arches_modular_reports/ResourceReport/utils/graph-nodes.ts";
import { resolveWorkspaces } from "@/arches_modular_reports/ResourceReport/utils/resolve-workspaces.ts";

import type { Component } from "vue";
import type {
    EditTileRequest,
    ReportData,
    ResourceReportConfig,
} from "@/arches_modular_reports/ResourceReport/types.ts";

const BUILT_IN_WORKSPACE_COMPONENTS: Record<string, Component> = {
    [REPORT_WORKSPACE]: ReportWorkspace,
    [DATA_WORKSPACE]: DataWorkspace,
    [GRAPH_WORKSPACE]: GraphWorkspace,
};

const { component, resourceInstanceId } = defineProps<{
    component: { component: string; config: ResourceReportConfig };
    resourceInstanceId: string;
}>();

const graphSlug = inject("graphSlug") as string;

const { $gettext } = useGettext();
const reportContext = useReportContext(resourceInstanceId);
const graphWidgetConfigs = useGraphWidgetConfigs(graphSlug);
const changeSet = useResourceChangeSet(graphSlug, resourceInstanceId);
const { context, isTransitioning, transitionError, transitionLifecycle } =
    reportContext;

const selectedWorkspaceId = ref<string | null>(null);
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

const workspaces = computed(() =>
    resolveWorkspaces(component.config.workspaces ?? [], {
        canEdit: canEdit.value,
        activeLanguage: context.value?.language ?? "",
    }),
);

const activeWorkspace = computed(
    () =>
        workspaces.value.find(
            (workspace) => workspace.id === selectedWorkspaceId.value,
        ) ?? workspaces.value[0],
);

const graphNodesByAlias = computed(() =>
    indexGraphNodes(graphWidgetConfigs.nodegroupWidgetConfigs.value ?? {}),
);

const folioLocationsByNodegroupAlias = computed(() =>
    folioLocations(
        component.config.workspaces ?? [],
        context.value?.language ?? "",
    ),
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
        graphNodesByAlias: graphNodesByAlias.value,
        folioLocations: folioLocationsByNodegroupAlias.value,
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

const activeWorkspaceComponentName = computed(
    () => activeWorkspace.value?.component,
);

const activeWorkspaceComponent = computed(() => {
    const componentName = activeWorkspaceComponentName.value;
    if (componentName === undefined) {
        return null;
    }
    return (
        BUILT_IN_WORKSPACE_COMPONENTS[componentName] ??
        loadComponent(componentName)
    );
});

watch(canEdit, (isEditable) => {
    if (!isEditable) {
        closeEditor();
    }
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
        v-if="fetchError && reportData === null"
        severity="error"
    >
        <span>
            {{
                $gettext(
                    "Unable to load this report: %{message}",
                    {
                        message: fetchError.message,
                    },
                    true,
                )
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
        v-else-if="reportData && activeWorkspace"
        class="resource-report"
        :dir="context?.language_dir"
    >
        <WorkspaceStrip
            v-if="workspaces.length > 1"
            :workspaces="workspaces"
            :active-workspace-id="activeWorkspace.id"
            @select-workspace="selectedWorkspaceId = $event"
        />
        <p
            v-if="activeWorkspace.description"
            class="resource-report-caption"
        >
            {{ activeWorkspace.description }}
        </p>
        <ReportHeader
            :report-data="reportData"
            :header-config="component.config.header ?? {}"
            :is-transitioning="isTransitioning"
            @transition-lifecycle="transitionLifecycle"
        />
        <Message
            v-if="fetchError"
            severity="error"
        >
            <span>
                {{
                    $gettext(
                        "Unable to refresh this report: %{message}",
                        {
                            message: fetchError.message,
                        },
                        true,
                    )
                }}
            </span>
        </Message>
        <Message
            v-if="transitionError"
            severity="error"
        >
            <span>
                {{
                    $gettext(
                        "Unable to change the lifecycle state: %{message}",
                        {
                            message: transitionError.message,
                        },
                        true,
                    )
                }}
            </span>
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
            v-if="hasPendingChanges"
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
    block-size: 100%;
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
    min-block-size: 0;
}

.resource-report-loading {
    display: flex;
    flex-direction: column;
    gap: 1.6rem;
    padding: 1.6rem;
}
</style>
