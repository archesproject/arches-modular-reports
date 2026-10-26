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
import { useFolioNavigation } from "@/arches_modular_reports/ResourceReport/composables/useFolioNavigation.ts";
import { useGraphWidgetConfigs } from "@/arches_modular_reports/ResourceReport/composables/useGraphWidgetConfigs.ts";
import { REPORT_DATA_KEY } from "@/arches_modular_reports/ResourceReport/composables/useReportData.ts";
import { useReportContext } from "@/arches_modular_reports/ResourceReport/composables/useReportContext.ts";
import { useResourceChangeSet } from "@/arches_modular_reports/ResourceReport/composables/useResourceChangeSet.ts";
import {
    componentPaths,
    folioLocations,
} from "@/arches_modular_reports/ResourceReport/utils/component-tree.ts";
import { indexGraphNodes } from "@/arches_modular_reports/ResourceReport/utils/graph-nodes.ts";

import type {
    ComponentNode,
    EditTileRequest,
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
const { context, isTransitioning, transitionError, transitionLifecycle } =
    reportContext;

const editorTarget = ref<EditTileRequest | null>(null);
const editorCount = ref(0);

const childNodes = computed(() => component.config.components ?? []);

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
    folioLocations(childNodes.value, context.value?.language ?? ""),
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
            isAvailable: editorCount.value > 0,
            open: openEditor,
            close: closeEditor,
            register: registerEditor,
        },
        lifecycle: {
            isTransitioning: isTransitioning.value,
            transitionError: transitionError.value,
            transition: transitionLifecycle,
        },
        folioNavigation,
    };
});

provide(REPORT_DATA_KEY, reportData);

watch(canEdit, (isEditable) => {
    if (!isEditable) {
        closeEditor();
    }
});

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
    display: flex;
    flex-direction: column;
    block-size: 100%;
    background: var(--p-content-background);
}

.resource-report-loading {
    display: flex;
    flex-direction: column;
    gap: 1.6rem;
    padding: 1.6rem;
}
</style>
