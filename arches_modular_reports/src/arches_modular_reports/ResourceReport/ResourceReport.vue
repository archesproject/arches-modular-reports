<script setup lang="ts">
import {
    computed,
    inject,
    onMounted,
    onUnmounted,
    provide,
    ref,
    watch,
    watchEffect,
} from "vue";
import { useGettext } from "vue3-gettext";

import Message from "openvue/message";
import Skeleton from "openvue/skeleton";

import {
    loadComponent,
    preloadComponents,
} from "@/arches_modular_reports/ModularReport/utils.ts";
import DeletedResourceNotice from "@/arches_modular_reports/ResourceReport/components/DeletedResourceNotice.vue";
import { useEditLinksPreference } from "@/arches_modular_reports/ResourceReport/composables/useEditLinksPreference.ts";
import { useFolioNavigation } from "@/arches_modular_reports/ResourceReport/composables/useFolioNavigation.ts";
import { useGraphWidgetConfigs } from "@/arches_modular_reports/ResourceReport/composables/useGraphWidgetConfigs.ts";
import { REPORT_DATA_KEY } from "@/arches_modular_reports/ResourceReport/composables/useReportData.ts";
import { useReportContext } from "@/arches_modular_reports/ResourceReport/composables/useReportContext.ts";
import { useResourceChangeSet } from "@/arches_modular_reports/ResourceReport/composables/useResourceChangeSet.ts";
import {
    componentPaths,
    folioLocations,
    reportTabGroups,
    withoutHiddenCards,
} from "@/arches_modular_reports/ResourceReport/utils/component-tree.ts";
import { indexGraphNodes } from "@/arches_modular_reports/ResourceReport/utils/graph-nodes.ts";

import type {
    ComponentNode,
    EditTileRequest,
    ReportContext,
    ReportData,
    ResourceReportConfig,
} from "@/arches_modular_reports/ResourceReport/types.ts";

const { component, resourceInstanceId } = defineProps<{
    component: ComponentNode<ResourceReportConfig>;
    resourceInstanceId: string;
}>();

const graphSlug = inject("graphSlug") as string;

const { $gettext } = useGettext();
const reportContext = useReportContext(resourceInstanceId);
const graphWidgetConfigs = useGraphWidgetConfigs(graphSlug);
const changeSet = useResourceChangeSet(graphSlug, resourceInstanceId);
const folioNavigation = useFolioNavigation(
    graphWidgetConfigs.nodegroupWidgetConfigs,
);
const { areEditLinksShown, toggleEditLinks } = useEditLinksPreference();
const {
    context,
    isTransitioning,
    transitionError,
    transitionLifecycle,
    reloadContext,
} = reportContext;

const editorTarget = ref<EditTileRequest | null>(null);
const editorCount = ref(0);
const deletedResource = ref<{
    name: string;
    context: ReportContext;
} | null>(null);

const childNodes = computed(() =>
    withoutHiddenCards(
        component.config.components ?? [],
        graphWidgetConfigs.nodegroupWidgetConfigs.value ?? {},
    ),
);

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

const graphNodesByAlias = computed(() =>
    indexGraphNodes(graphWidgetConfigs.nodegroupWidgetConfigs.value ?? {}),
);

const folioLocationsByNodegroupAlias = computed(() =>
    folioLocations(
        childNodes.value,
        context.value?.language ?? "",
        context.value?.default_language ?? "",
    ),
);

const reportTabs = computed(() =>
    reportTabGroups(
        childNodes.value,
        context.value?.language ?? "",
        context.value?.default_language ?? "",
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
        reportTabs: reportTabs.value,
        resource: changeSet.workingResource.value,
        canEdit: canEdit.value,
        changeSet,
        editor: {
            target: editorTarget.value,
            isAvailable: editorCount.value > 0,
            open: openEditor,
            close: closeEditor,
            register: registerEditor,
        },
        editLinks: {
            isShown: areEditLinksShown.value,
            toggle: toggleEditLinks,
        },
        lifecycle: {
            isTransitioning: isTransitioning.value,
            transitionError: transitionError.value,
            transition: transitionLifecycle,
        },
        folioNavigation,
        markDeleted,
    };
});

provide(REPORT_DATA_KEY, reportData);

watch(canEdit, (isEditable) => {
    if (!isEditable) {
        closeEditor();
    }
});

watch(
    () => changeSet.isSaving.value,
    (isSaving, wasSaving) => {
        if (wasSaving && !isSaving && changeSet.saveError.value === null) {
            reloadContext();
        }
    },
);

watchEffect(() => {
    preloadComponents(componentPaths(childNodes.value));
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

function registerEditor(): () => void {
    editorCount.value += 1;
    return () => {
        editorCount.value -= 1;
    };
}

function markDeleted(): void {
    if (context.value === null || changeSet.workingResource.value === null) {
        return;
    }
    deletedResource.value = {
        name: changeSet.workingResource.value.name?.trim() ?? "",
        context: context.value,
    };
    changeSet.discardAll();
    closeEditor();
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
    <DeletedResourceNotice
        v-else-if="deletedResource"
        :resource-name="deletedResource.name"
        :context="deletedResource.context"
    />
    <div
        v-else-if="reportData"
        class="resource-report"
        :dir="context?.language_dir"
    >
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
            v-if="changeSet.addError.value"
            severity="error"
        >
            <span>
                {{
                    $gettext(
                        "Unable to add an entry: %{message}",
                        {
                            message: changeSet.addError.value.message,
                        },
                        true,
                    )
                }}
            </span>
        </Message>
        <component
            :is="loadComponent(childNode.component)"
            v-for="(childNode, childIndex) in childNodes"
            :key="childIndex"
            :component="childNode"
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
    --p-text-color: var(--p-surface-800);
    --resource-report-panel-background: var(--p-surface-50);
    --resource-report-muted-background: var(--p-surface-100);
    --resource-report-bar-background: var(--p-surface-200);
    --resource-report-bar-border-color: var(--p-surface-300);
    --resource-report-row-open-background: var(--p-blue-100);
    --resource-report-row-hover-background: var(--p-blue-50);
    --resource-report-accent-background: color-mix(
        in srgb,
        var(--p-primary-color) 12%,
        transparent
    );
    --resource-report-edited-background: color-mix(
        in srgb,
        var(--p-blue-500) 12%,
        transparent
    );
    --resource-report-edited-color: var(--p-blue-600);
    --resource-report-deleted-background: color-mix(
        in srgb,
        var(--p-red-500) 10%,
        transparent
    );
    --resource-report-deleted-color: var(--p-red-600);
    --resource-report-pending-background: var(--p-yellow-200);
    --resource-report-pending-border-color: var(--p-yellow-400);
    --resource-report-pending-color: var(--p-surface-900);
    --resource-report-drawer-trigger-open-background: var(--p-primary-700);
    --resource-report-drawer-trigger-open-color: var(
        --p-primary-contrast-color
    );
    --resource-report-drawer-header-background: color-mix(
        in srgb,
        var(--p-surface-100),
        var(--p-surface-200)
    );
    --resource-report-bar-block-size: 4rem;
    --map-header-expand-button-pressed-background: var(
        --resource-report-drawer-trigger-open-background
    );
    --map-header-expand-button-pressed-color: var(
        --resource-report-drawer-trigger-open-color
    );
    --resource-instance-multiselect-chip-background: var(--p-primary-700);
    --resource-instance-multiselect-chip-color: var(--p-surface-0);
    --resource-instance-multiselect-chip-button-color: var(--p-surface-0);
    --resource-instance-multiselect-chip-button-hover-background: color-mix(
        in srgb,
        var(--p-surface-0) 20%,
        transparent
    );
    --map-component-viewer-block-size: 50rem;

    display: flex;
    flex-direction: column;
    block-size: 100%;
    background: var(--p-content-background);
    color: var(--p-text-color);
}

.arches-dark .resource-report {
    --p-text-color: var(--p-surface-0);
    --resource-report-panel-background: var(--p-surface-900);
    --resource-report-muted-background: var(--p-surface-800);
    --resource-report-bar-background: var(--p-surface-950);
    --resource-report-bar-border-color: var(--p-surface-700);
    --resource-report-row-open-background: var(--p-blue-950);
    --resource-report-row-hover-background: var(--p-surface-700);
    --resource-report-accent-background: color-mix(
        in srgb,
        var(--p-primary-color) 22%,
        transparent
    );
    --resource-report-edited-background: color-mix(
        in srgb,
        var(--p-blue-500) 16%,
        transparent
    );
    --resource-report-edited-color: var(--p-blue-300);
    --resource-report-deleted-background: color-mix(
        in srgb,
        var(--p-red-500) 16%,
        transparent
    );
    --resource-report-deleted-color: var(--p-red-300);
    --resource-report-pending-background: color-mix(
        in srgb,
        var(--p-yellow-500) 16%,
        transparent
    );
    --resource-report-pending-border-color: color-mix(
        in srgb,
        var(--p-yellow-500) 40%,
        transparent
    );
    --resource-report-pending-color: var(--p-surface-0);
    --resource-report-drawer-trigger-open-color: var(--p-surface-0);
    --resource-report-drawer-header-background: color-mix(
        in srgb,
        var(--p-surface-800),
        var(--p-surface-900)
    );
}

.resource-report :deep(.p-button-link),
.resource-report :deep(.p-button-text),
.resource-report :deep(.p-button-link:not(:disabled):hover),
.resource-report :deep(.p-button-text:not(:disabled):hover) {
    border: none;
}

.resource-report :deep(.resource-instance-link) {
    font-weight: 600;
}

.resource-report :deep(.p-button-link),
.resource-report :deep(.p-button-text) {
    line-height: 1.2;
}

.resource-report-loading {
    display: flex;
    flex-direction: column;
    gap: 1.6rem;
    padding: 1.6rem;
}
</style>
