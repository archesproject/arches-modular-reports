<script setup lang="ts">
import { computed, watchEffect, provide, ref } from "vue";
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
} from "@/arches_modular_reports/ModularReport/api.ts";

import { DEFAULT_ERROR_TOAST_LIFE } from "@/arches_modular_reports/constants.ts";
import { importComponents } from "@/arches_modular_reports/ModularReport/utils.ts";
import ResourceEditor from "@/arches_modular_reports/ModularReport/components/ResourceEditor/ResourceEditor.vue";

import type { Ref } from "vue";
import type {
    ComponentLookup,
    NamedSection,
    NodePresentationLookup,
} from "@/arches_modular_reports/ModularReport/types";

const toast = useToast();
const { $gettext } = useGettext();
const componentLookup: ComponentLookup = {};

const { graphSlug, resourceInstanceId } = defineProps<{
    graphSlug: string;
    resourceInstanceId: string;
}>();

provide("graphSlug", graphSlug);
provide("resourceInstanceId", resourceInstanceId);

const nodePresentationLookup: Ref<NodePresentationLookup | undefined> = ref();
provide("nodePresentationLookup", nodePresentationLookup);

const userCanEditResourceInstance = ref(false);
provide("userCanEditResourceInstance", userCanEditResourceInstance);

const selectedNodegroupAlias = ref<string>();
function setSelectedNodegroupAlias(nodegroupAlias: string | undefined) {
    selectedNodegroupAlias.value = nodegroupAlias;
}
provide("selectedNodegroupAlias", {
    selectedNodegroupAlias,
    setSelectedNodegroupAlias,
});

// string: persisted tile
// null: dummy (blank) tile
// undefined: nothing selected; hide editor
const selectedTileId = ref<string | null | undefined>(undefined);
function setSelectedTileId(tileId?: string | null) {
    selectedTileId.value = tileId;
}
provide("selectedTileId", { selectedTileId, setSelectedTileId });

const reportKey = ref(0);
const editorKey = ref(0);

const config: Ref<NamedSection> = ref({
    name: $gettext("Loading data"),
    components: [],
});

const gutterVisibility = computed(() => {
    return selectedNodegroupAlias.value ? "visible" : "hidden";
});

watchEffect(async () => {
    try {
        await Promise.all([
            fetchNodePresentation(resourceInstanceId).then((data) => {
                nodePresentationLookup.value = data;
            }),
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
    setSelectedNodegroupAlias(undefined);
    setSelectedTileId(undefined);
    editorKey.value++;
}
</script>

<template>
    <Splitter>
        <SplitterPanel style="overflow: auto">
            <div :key="reportKey">
                <component
                    :is="componentLookup[component.component].component"
                    v-for="component in config.components"
                    :key="componentLookup[component.component].key"
                    :component
                    :resource-instance-id
                />
            </div>
        </SplitterPanel>
        <SplitterPanel
            v-show="selectedNodegroupAlias"
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
                <ResourceEditor
                    v-if="userCanEditResourceInstance"
                    @save="reportKey++"
                />
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
