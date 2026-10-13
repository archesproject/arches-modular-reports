<script setup lang="ts">
import { computed, ref } from "vue";
import { useGettext } from "vue3-gettext";

import IconField from "openvue/iconfield";
import InputIcon from "openvue/inputicon";
import InputText from "openvue/inputtext";
import Splitter from "openvue/splitter";
import SplitterPanel from "openvue/splitterpanel";

import DataFolio from "@/arches_modular_reports/ResourceReport/components/DataWorkspace/components/DataFolio.vue";
import EditorPanel from "@/arches_modular_reports/ResourceReport/components/EditorPanel.vue";
import ReportPlaceholder from "@/arches_modular_reports/ResourceReport/components/ReportPlaceholder.vue";

import { childNodegroupAliases } from "@/arches_modular_reports/ResourceReport/utils/graph-nodes.ts";
import { nodegroupTiles } from "@/arches_modular_reports/ResourceReport/utils/tiles.ts";

import type {
    ReportData,
    ReportWorkspaceConfig,
} from "@/arches_modular_reports/ResourceReport/types.ts";

const SPLITTER_STATE_KEY = "arches-modular-reports-data-workspace";
const MINIMUM_PANE_SIZE = 20;
const BROWSER_PANE_SIZE = 40;
const EDITOR_PANE_SIZE = 60;

const { reportData } = defineProps<{
    workspaceConfig: ReportWorkspaceConfig;
    reportData: ReportData;
}>();

const { $gettext } = useGettext();

const filterText = ref("");

const folios = computed(() =>
    childNodegroupAliases(reportData.nodegroupWidgetConfigs, null).map(
        (nodegroupAlias) => ({
            nodegroupAlias,
            tiles: nodegroupTiles(
                reportData.resource.aliased_data[nodegroupAlias],
            ),
        }),
    ),
);
</script>

<template>
    <Splitter
        class="data-workspace"
        state-storage="local"
        :state-key="SPLITTER_STATE_KEY"
    >
        <SplitterPanel
            class="data-workspace-pane data-workspace-browser"
            :size="BROWSER_PANE_SIZE"
            :min-size="MINIMUM_PANE_SIZE"
        >
            <IconField>
                <InputIcon class="pi pi-search" />
                <InputText
                    v-model="filterText"
                    class="data-workspace-filter"
                    :placeholder="$gettext('Filter...')"
                    :aria-label="$gettext('Filter the data')"
                />
            </IconField>
            <DataFolio
                v-for="folio in folios"
                :key="folio.nodegroupAlias"
                :nodegroup-alias="folio.nodegroupAlias"
                :nodegroup-widget-configs="reportData.nodegroupWidgetConfigs"
                :tiles="folio.tiles"
                :parent-tile-id="null"
                :change-set="reportData.changeSet"
                :filter-text="filterText"
                :selected-tile-id="reportData.editor.target?.tileId ?? null"
                @edit-tile="reportData.editor.open"
            />
        </SplitterPanel>
        <SplitterPanel
            class="data-workspace-pane data-workspace-editor"
            :size="EDITOR_PANE_SIZE"
            :min-size="MINIMUM_PANE_SIZE"
        >
            <EditorPanel
                v-if="reportData.editor.target"
                :target="reportData.editor.target"
                :report-data="reportData"
            />
            <ReportPlaceholder
                v-else
                icon="pi pi-pencil"
                :message="
                    $gettext(
                        'Select an entry in the data browser to begin editing.',
                    )
                "
            />
        </SplitterPanel>
    </Splitter>
</template>

<style scoped>
.data-workspace {
    border: none;
    border-radius: 0;
}

.data-workspace-pane {
    display: flex;
    flex-direction: column;
    min-width: 0;
    overflow-y: auto;
}

.data-workspace-browser {
    gap: 1.2rem;
    padding: 1.6rem;
}

.data-workspace-filter {
    width: 100%;
}

.data-workspace-editor {
    background: var(
        --p-resource-report-aside-background,
        var(--p-content-hover-background)
    );
}
</style>
