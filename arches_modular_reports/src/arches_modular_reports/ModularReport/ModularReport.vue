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
    fetchLanguageSettings,
} from "@/arches_modular_reports/ModularReport/api.ts";

import { DEFAULT_ERROR_TOAST_LIFE } from "@/arches_modular_reports/constants.ts";
import { importComponents } from "@/arches_modular_reports/ModularReport/utils.ts";
import ResourceEditor from "@/arches_modular_reports/ModularReport/components/ResourceEditor/ResourceEditor.vue";

import type { Ref } from "vue";
import type {
    ComponentLookup,
    NamedSection,
    NodePresentationLookup,
    LanguageSettings,
} from "@/arches_modular_reports/ModularReport/types";

const toast = useToast();
const { $gettext } = useGettext();
const componentLookup: ComponentLookup = {};

// Prevents spamming i18n functions on panel drag
const EDITOR = $gettext("Editor");
const CLOSE_EDITOR = $gettext("Close editor");

const { graphSlug, resourceInstanceId, reportConfigSlug } = defineProps<{
    graphSlug: string;
    resourceInstanceId: string;
    reportConfigSlug?: string;
}>();

provide("graphSlug", graphSlug);
provide("resourceInstanceId", resourceInstanceId);

const nodePresentationLookup: Ref<NodePresentationLookup | undefined> = ref();
provide("nodePresentationLookup", nodePresentationLookup);

const userCanEditResourceInstance = ref(false);
provide("userCanEditResourceInstance", userCanEditResourceInstance);

const languageSettings = ref<Partial<LanguageSettings>>({});
provide("languageSettings", languageSettings);

const selectedNodegroupAlias = ref<string | null>();
function setSelectedNodegroupAlias(nodegroupAlias: string | null | undefined) {
    selectedNodegroupAlias.value = nodegroupAlias;
}
provide("selectedNodegroupAlias", {
    selectedNodegroupAlias,
    setSelectedNodegroupAlias,
});

const selectedNodeAlias = ref<string | null>();
function setSelectedNodeAlias(nodeAlias: string | null) {
    selectedNodeAlias.value = nodeAlias;
}
provide("selectedNodeAlias", {
    selectedNodeAlias,
    setSelectedNodeAlias,
});

const selectedTileId = ref<string | null | undefined>();
function setSelectedTileId(tileId?: string | null) {
    selectedTileId.value = tileId;
}
provide("selectedTileId", {
    selectedTileId,
    setSelectedTileId,
});

const selectedTilePath = ref<string[] | null>();
function setSelectedTilePath(path: string[] | null) {
    selectedTilePath.value = path;
}
provide("selectedTilePath", {
    selectedTilePath,
    setSelectedTilePath,
});

const shouldShowEditor = ref(false);
function setShouldShowEditor(shouldShow: boolean) {
    shouldShowEditor.value = shouldShow;
}
provide("shouldShowEditor", {
    shouldShowEditor,
    setShouldShowEditor,
});

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
            fetchLanguageSettings().then((data) => {
                languageSettings.value = {
                    ACTIVE_LANGUAGE: data.language,
                    ACTIVE_LANGUAGE_DIRECTION: data.language_dir,
                };
            }),
            fetchReportConfig(resourceInstanceId, reportConfigSlug).then(
                (data) => {
                    importComponents([data], componentLookup);
                    config.value = data;
                },
            ),
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
    setSelectedNodegroupAlias(null);
    setSelectedTileId(null);
    setSelectedTilePath(null);
    setShouldShowEditor(false);

    editorKey.value++;
}
</script>

<template>
    <Splitter style="overflow: hidden">
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
            v-show="shouldShowEditor"
            style="overflow: auto"
            :size="30"
        >
            <Panel
                :key="editorKey"
                toggleable
                :toggle-button-props="{
                    ariaLabel: CLOSE_EDITOR,
                    severity: 'secondary',
                }"
                :style="{
                    overflow: 'auto',
                    height: '100%',
                    border: 'none',
                }"
                :header="EDITOR"
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
    border: 0;
    border-radius: 0;
}

:deep(.p-splitter-gutter) {
    visibility: v-bind(gutterVisibility);
}

:deep(.p-panel-content) {
    padding: 0;
}
@media print {
    .p-splitter {
        position: unset;
    }
    button,
    :deep(svg),
    :deep(button) {
        display: none;
    }
}
</style>
