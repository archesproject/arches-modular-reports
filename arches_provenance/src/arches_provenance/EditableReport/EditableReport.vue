<script setup lang="ts">
import { computed, inject, onMounted, provide, ref } from "vue";
import { useGettext } from "vue3-gettext";

import Panel from "primevue/panel";
import Splitter from "primevue/splitter";
import SplitterPanel from "primevue/splitterpanel";
import Toast from "primevue/toast";
import { useToast } from "primevue/usetoast";

import {
    fetchNodePresentation,
    fetchReportConfig,
    fetchUserResourcePermissions,
} from "@/arches_provenance/EditableReport/api.ts";
import { DEFAULT_ERROR_TOAST_LIFE } from "@/arches_provenance/constants.ts";
import { importComponents } from "@/arches_provenance/EditableReport/utils.ts";
import ResourceEditor from "@/arches_provenance/EditableReport/components/ResourceEditor/ResourceEditor.vue";

import type { Ref } from "vue";
import type {
    ComponentLookup,
    NamedSection,
    NodePresentationLookup,
} from "@/arches_provenance/EditableReport/types";

const toast = useToast();
const { $gettext } = useGettext();
const componentLookup: ComponentLookup = {};

const resourceInstanceId = inject("resourceInstanceId") as string;

const nodePresentationLookup: Ref<NodePresentationLookup | undefined> = ref();
provide("nodePresentationLookup", nodePresentationLookup);

const userCanEditResourceInstance = ref(false);
provide("userCanEditResourceInstance", userCanEditResourceInstance);

const editorKey = ref(0);

const selectedNodeAlias = ref<string | null>(null);
function setSelectedNodeAlias(nodeAlias: string | null) {
    selectedNodeAlias.value = nodeAlias;
}
provide("selectedNodeAlias", { selectedNodeAlias, setSelectedNodeAlias });

const selectedTileId = ref<string | null>(null);
function setSelectedTileId(tileId: string | null) {
    selectedTileId.value = tileId;
}
provide("selectedTileId", { selectedTileId, setSelectedTileId });

const config: Ref<NamedSection> = ref({
    name: $gettext("Loading data"),
    components: [],
});

const gutterVisibility = computed(() => {
    return selectedNodeAlias.value ? "visible" : "hidden";
});

onMounted(async () => {
    if (!resourceInstanceId) {
        return;
    }
    try {
        await Promise.all([
            fetchNodePresentation(resourceInstanceId).then(
                (data) => (nodePresentationLookup.value = data),
            ),
            fetchUserResourcePermissions(resourceInstanceId).then((data) => {
                userCanEditResourceInstance.value = data.edit;
            }),
            fetchReportConfig(resourceInstanceId).then((data) => {
                importComponents([data], componentLookup);
                config.value = data;
            }),
        ]);
    } catch (error) {
        toast.add({
            severity: "error",
            life: DEFAULT_ERROR_TOAST_LIFE,
            summary: $gettext("Unable to fetch resource"),
            detail: (error as Error).message ?? error,
        });
        return;
    }
});

function closeEditor() {
    selectedNodeAlias.value = null;
    selectedTileId.value = null;
}
</script>

<template>
    <Splitter>
        <SplitterPanel style="overflow: auto">
            <component
                :is="componentLookup[component.component].component"
                v-for="component in config.components"
                :key="componentLookup[component.component].key"
                :component
                :resource-instance-id
            />
        </SplitterPanel>
        <SplitterPanel
            v-show="selectedTileId"
            style="overflow: auto"
        >
            <Panel
                :key="editorKey"
                toggleable
                :toggle-button-props="{
                    ariaLabel: $gettext('Close editor'),
                    severity: 'secondary',
                }"
                :style="{
                    overflow: 'auto',
                    height: '100%',
                    border: 'none',
                }"
                :header="$gettext('Editor')"
                @toggle="closeEditor"
            >
                <template #toggleicon>
                    <i
                        class="pi pi-times"
                        aria-hidden="true"
                    />
                </template>
                <ResourceEditor />
            </Panel>
        </SplitterPanel>
    </Splitter>

    <Toast />
</template>

<style scoped>
.p-splitter {
    position: absolute;
    height: 100%;
    width: 100%;
    display: flex;
}

:deep(.p-splitter-gutter) {
    visibility: v-bind(gutterVisibility);
}
</style>
