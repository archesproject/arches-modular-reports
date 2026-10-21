<script setup lang="ts">
import { computed, nextTick, ref } from "vue";

import Splitter from "openvue/splitter";
import SplitterPanel from "openvue/splitterpanel";
import Tab from "openvue/tab";
import TabList from "openvue/tablist";
import TabPanel from "openvue/tabpanel";
import TabPanels from "openvue/tabpanels";
import Tabs from "openvue/tabs";

import EditorPanel from "@/arches_modular_reports/ResourceReport/components/EditorPanel.vue";
import HomeDrawer from "@/arches_modular_reports/ResourceReport/components/ReportWorkspace/components/HomeDrawer/HomeDrawer.vue";
import KeyDataSummary from "@/arches_modular_reports/ResourceReport/components/ReportWorkspace/components/KeyDataSummary.vue";
import ReportFolio from "@/arches_modular_reports/ResourceReport/components/ReportWorkspace/components/ReportFolio.vue";

import { nodegroupLineage } from "@/arches_modular_reports/ResourceReport/utils/graph-nodes.ts";
import { localizeLabel } from "@/arches_modular_reports/ResourceReport/utils/localize-label.ts";
import { nodegroupTiles } from "@/arches_modular_reports/ResourceReport/utils/tiles.ts";

import type { ComponentPublicInstance } from "vue";
import type {
    ReportData,
    ReportWorkspaceConfig,
} from "@/arches_modular_reports/ResourceReport/types.ts";

const SPLITTER_STATE_KEY = "arches-modular-reports-report-workspace";
const MINIMUM_PANE_SIZE = 20;
const MAIN_PANE_SIZE = 60;
const HOME_PANE_SIZE = 40;
const FULL_PANE_SIZE = 100;

const { workspaceConfig, reportData } = defineProps<{
    workspaceConfig: ReportWorkspaceConfig;
    reportData: ReportData;
}>();

const folioAnchors = new Map<string, HTMLElement>();
const activeTabIndex = ref(0);
const flashedNodegroupAlias = ref<string | null>(null);

const hasAside = computed(
    () => workspaceConfig.home !== null || reportData.editor.target !== null,
);

const mainPaneSize = computed(() => {
    if (hasAside.value) {
        return MAIN_PANE_SIZE;
    }
    return FULL_PANE_SIZE;
});

const tabs = computed(() =>
    workspaceConfig.tabs.map((tabConfig) => ({
        label: localizeLabel(tabConfig.label, reportData.context.language),
        sections: tabConfig.sections.map((sectionConfig) => ({
            label: localizeLabel(
                sectionConfig.label,
                reportData.context.language,
            ),
            icon: sectionConfig.icon,
            folios: sectionConfig.folios.map((folioConfig) => ({
                nodegroupAlias: folioConfig.nodegroup_alias,
                tiles: nodegroupTiles(
                    reportData.resource.aliased_data[
                        folioConfig.nodegroup_alias
                    ],
                ),
            })),
        })),
    })),
);

const tabIndexesByNodegroupAlias = computed(() => {
    const tabIndexes: Record<string, number> = {};
    tabs.value.forEach((tab, tabIndex) => {
        for (const section of tab.sections) {
            for (const folio of section.folios) {
                tabIndexes[folio.nodegroupAlias] ??= tabIndex;
            }
        }
    });
    return tabIndexes;
});

async function jumpToNode(nodeAlias: string): Promise<void> {
    const targetNodegroupAlias = nodegroupLineage(
        reportData.nodegroupWidgetConfigs,
        reportData.graphNodesByAlias[nodeAlias].nodegroupAlias,
    ).find(
        (nodegroupAlias) => nodegroupAlias in tabIndexesByNodegroupAlias.value,
    );
    if (targetNodegroupAlias === undefined) {
        return;
    }

    flashedNodegroupAlias.value = null;
    activeTabIndex.value =
        tabIndexesByNodegroupAlias.value[targetNodegroupAlias];
    await nextTick();

    folioAnchors.get(targetNodegroupAlias)?.scrollIntoView({ block: "center" });
    flashedNodegroupAlias.value = targetNodegroupAlias;
}

function registerFolioAnchor(
    nodegroupAlias: string,
    folioAnchor: Element | ComponentPublicInstance | null,
): void {
    if (folioAnchor instanceof HTMLElement) {
        folioAnchors.set(nodegroupAlias, folioAnchor);
    } else {
        folioAnchors.delete(nodegroupAlias);
    }
}

function clearFlash(): void {
    flashedNodegroupAlias.value = null;
}
</script>

<template>
    <Splitter
        :key="String(hasAside)"
        class="report-workspace"
        state-storage="local"
        :state-key="hasAside ? SPLITTER_STATE_KEY : undefined"
    >
        <SplitterPanel
            class="report-workspace-pane"
            :size="mainPaneSize"
            :min-size="MINIMUM_PANE_SIZE"
        >
            <Tabs
                v-model:value="activeTabIndex"
                :lazy="true"
                :show-navigators="false"
            >
                <TabList v-if="tabs.length > 1">
                    <Tab
                        v-for="(tab, tabIndex) in tabs"
                        :key="tabIndex"
                        :value="tabIndex"
                    >
                        <span>{{ tab.label }}</span>
                    </Tab>
                </TabList>
                <TabPanels>
                    <TabPanel
                        v-for="(tab, tabIndex) in tabs"
                        :key="tabIndex"
                        class="report-workspace-tab"
                        :value="tabIndex"
                    >
                        <section
                            v-for="(section, sectionIndex) in tab.sections"
                            :key="sectionIndex"
                            class="report-workspace-section"
                        >
                            <h3
                                v-if="section.label"
                                class="report-workspace-section-label"
                            >
                                <i
                                    v-if="section.icon"
                                    aria-hidden="true"
                                    :class="section.icon"
                                />
                                <span>{{ section.label }}</span>
                            </h3>
                            <div
                                v-for="folio in section.folios"
                                :key="folio.nodegroupAlias"
                                :ref="
                                    (folioAnchor) =>
                                        registerFolioAnchor(
                                            folio.nodegroupAlias,
                                            folioAnchor,
                                        )
                                "
                                class="report-workspace-folio"
                                :class="{
                                    'report-workspace-folio-flash':
                                        flashedNodegroupAlias ===
                                        folio.nodegroupAlias,
                                }"
                                @animationend.self="clearFlash"
                            >
                                <ReportFolio
                                    :nodegroup-alias="folio.nodegroupAlias"
                                    :tiles="folio.tiles"
                                    :parent-tile-id="null"
                                    :report-data="reportData"
                                />
                            </div>
                        </section>
                    </TabPanel>
                </TabPanels>
            </Tabs>
        </SplitterPanel>
        <SplitterPanel
            v-if="hasAside"
            class="report-workspace-pane report-workspace-aside"
            :size="HOME_PANE_SIZE"
            :min-size="MINIMUM_PANE_SIZE"
        >
            <EditorPanel
                v-if="reportData.editor.target"
                :target="reportData.editor.target"
                :report-data="reportData"
            />
            <HomeDrawer
                v-else-if="workspaceConfig.home"
                :entries="workspaceConfig.home.drawer"
                :report-data="reportData"
            >
                <div class="report-workspace-home">
                    <KeyDataSummary
                        :summary="workspaceConfig.home.summary"
                        :report-data="reportData"
                        @jump-to-node="jumpToNode"
                    />
                </div>
            </HomeDrawer>
        </SplitterPanel>
    </Splitter>
</template>

<style scoped>
.report-workspace {
    border: none;
    border-radius: 0;
}

.report-workspace-pane {
    display: flex;
    flex-direction: column;
    min-inline-size: 0;
    overflow: auto;
}

.report-workspace-home {
    padding: 1.6rem;
}

.report-workspace-aside {
    background: var(--p-resource-report-aside-background);
}

.report-workspace-tab {
    display: flex;
    flex-direction: column;
    gap: 2.4rem;
    max-inline-size: 120rem;
}

.report-workspace-section {
    display: flex;
    flex-direction: column;
    gap: 1.6rem;
}

.report-workspace-section-label {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    margin: 0;
    padding-block-end: 0.8rem;
    border-block-end: 0.1rem solid var(--p-content-border-color);
    color: var(--p-text-color);
    font-size: 1.6rem;
    font-weight: 600;
}

.report-workspace-folio {
    border-radius: var(--p-content-border-radius);
}

.report-workspace-folio-flash {
    animation: report-workspace-folio-flash 1.6s ease-out;
}

@keyframes report-workspace-folio-flash {
    from {
        background: var(--p-highlight-background);
        box-shadow: 0 0 0 0.8rem var(--p-highlight-background);
    }
}

@media (prefers-reduced-motion: no-preference) {
    .report-workspace-pane {
        scroll-behavior: smooth;
    }
}
</style>
