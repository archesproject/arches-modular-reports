<script setup lang="ts">
import { useGettext } from "vue3-gettext";

import Splitter from "openvue/splitter";
import SplitterPanel from "openvue/splitterpanel";

import ReportPlaceholder from "@/arches_modular_reports/ResourceReport/components/ReportPlaceholder.vue";

import type {
    ReportData,
    ReportWorkspaceConfig,
} from "@/arches_modular_reports/ResourceReport/types.ts";

const SPLITTER_STATE_KEY = "arches-modular-reports-data-workspace";
const MINIMUM_PANE_SIZE = 20;
const BROWSER_PANE_SIZE = 40;
const EDITOR_PANE_SIZE = 60;

defineProps<{
    workspaceConfig: ReportWorkspaceConfig;
    reportData: ReportData;
}>();

const { $gettext } = useGettext();
</script>

<template>
    <Splitter
        class="data-workspace"
        state-storage="local"
        :state-key="SPLITTER_STATE_KEY"
    >
        <SplitterPanel
            class="data-workspace-pane"
            :size="BROWSER_PANE_SIZE"
            :min-size="MINIMUM_PANE_SIZE"
        >
            <ReportPlaceholder
                icon="pi pi-database"
                :message="$gettext('The data browser is not available yet.')"
            />
        </SplitterPanel>
        <SplitterPanel
            class="data-workspace-pane data-workspace-editor"
            :size="EDITOR_PANE_SIZE"
            :min-size="MINIMUM_PANE_SIZE"
        >
            <ReportPlaceholder
                icon="pi pi-pencil"
                :message="
                    $gettext(
                        'Select a branch from the browser to begin editing.',
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

.data-workspace-editor {
    background: var(
        --p-resource-report-aside-background,
        var(--p-content-hover-background)
    );
}
</style>
