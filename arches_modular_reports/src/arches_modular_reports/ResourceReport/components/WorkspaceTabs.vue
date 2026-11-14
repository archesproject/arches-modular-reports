    <script setup lang="ts">
import { computed } from "vue";

import Tab from "openvue/tab";
import TabList from "openvue/tablist";
import Tabs from "openvue/tabs";

import ReportExports from "@/arches_modular_reports/ResourceReport/components/ReportExports.vue";
import TabLabel from "@/arches_modular_reports/ResourceReport/components/TabLabel.vue";

import { loadComponent } from "@/arches_modular_reports/ModularReport/utils.ts";
import { useTabbedComponents } from "@/arches_modular_reports/ResourceReport/composables/useTabbedComponents.ts";
import { provideWorkspaceHeaderHost } from "@/arches_modular_reports/ResourceReport/composables/useWorkspaceHeaderHost.ts";

import type {
    ComponentNode,
    WorkspaceTabsConfig,
} from "@/arches_modular_reports/ResourceReport/types.ts";

const { component } = defineProps<{
    component: ComponentNode<WorkspaceTabsConfig>;
}>();

const { tabs, activeTabIndex, activeTab } = useTabbedComponents(
    () => component.config.components ?? [],
);

// A workspace with a main column (SplitPane) hosts the header there, so the
// aside starts at the top of the page; otherwise it renders full width here.
const headerHost = provideWorkspaceHeaderHost();

const bannerNodes = computed(() => component.config.banner ?? []);
</script>

<template>
    <div class="workspace-tabs">
        <Teleport
            :to="headerHost ?? 'body'"
            :disabled="headerHost === null"
        >
            <div class="workspace-tabs-header">
                <!-- The resource first, then the views of it. -->
                <component
                    :is="loadComponent(bannerNode.component)"
                    v-for="(bannerNode, bannerIndex) in bannerNodes"
                    :key="bannerIndex"
                    :component="bannerNode"
                />
                <div class="workspace-tabs-bar">
                    <Tabs
                        v-if="tabs.length > 1"
                        v-model:value="activeTabIndex"
                        class="workspace-tabs-strip"
                        :show-navigators="false"
                    >
                        <TabList>
                            <Tab
                                v-for="(tab, tabIndex) in tabs"
                                :key="tabIndex"
                                :value="tabIndex"
                            >
                                <TabLabel :tab="tab" />
                            </Tab>
                        </TabList>
                    </Tabs>
                    <ReportExports class="workspace-tabs-exports" />
                </div>
            </div>
        </Teleport>
        <component
            :is="loadComponent(activeTab.node.component)"
            v-if="activeTab"
            :key="activeTabIndex"
            :component="activeTab.node"
        />
    </div>
</template>

<style scoped>
.workspace-tabs {
    display: flex;
    flex: 1;
    flex-direction: column;
    min-block-size: 0;
}

/* Folder tabs on the left, export links right-justified, on one bar. The
   bar's bottom line is an inset shadow, so the tabs (painted over it) decide
   where it shows: under the inactive tabs, but not under the active one,
   which opens onto the workspace below. */
.workspace-tabs-bar {
    display: flex;
    align-items: flex-end;
    justify-content: flex-end;
    gap: 1.6rem;    
    background: var(--resource-report-bar-background);
    box-shadow: inset 0 -0.1rem 0 var(--resource-report-bar-border-color);
}

.workspace-tabs-bar .workspace-tabs-exports {
    flex-shrink: 0;
    align-self: center;
    padding-inline: 1rem;
}

.workspace-tabs-strip {
    flex: 1;
    min-inline-size: 0;
    --p-tabs-tablist-background: transparent;
    --p-tabs-tablist-border-width: 0;
    --p-tabs-tab-padding: 0 1.6rem;
    --p-tabs-tab-margin: 0;
    --p-tabs-tab-font-weight: 500;
    --p-tabs-tab-border-width: 0.1rem 0.1rem 0;
    --p-tabs-tab-border-color: var(--resource-report-bar-border-color);
    --p-tabs-tab-hover-border-color: var(--resource-report-bar-border-color);
    --p-tabs-tab-active-border-color: var(--resource-report-bar-border-color);
    --p-tabs-tab-background: var(--resource-report-muted-background);
    --p-tabs-tab-hover-background: var(--resource-report-panel-background);
    --p-tabs-tab-active-background: var(--p-content-background);
    --p-tabs-tab-color: var(--p-text-muted-color);
    --p-tabs-tab-hover-color: var(--p-text-color);
    --p-tabs-tab-active-color: var(--p-text-color);
    --p-tabs-active-bar-height: 0;
}

.workspace-tabs-strip :deep(.p-tablist-tab-list) {
    align-items: flex-end;
    gap: 0rem;
    border-block-end: none;
}

.workspace-tabs-strip :deep(.p-tab) {
    block-size: 3.4rem;
    font-size: 1.35rem;
    min-width: 11rem;
}

/* Neighbouring tabs share one border: each draws only its end side, after the
   first. */
.workspace-tabs-strip :deep(.p-tab + .p-tab) {
    border-inline-start-width: 0;
}

/* The bar's bottom line, drawn on the inactive tabs that cover it. */
.workspace-tabs-strip :deep(.p-tab:not(.p-tab-active)) {
    border-block-end: 0.1rem solid var(--resource-report-bar-border-color);
}

/* A primary edge on top marks the active tab without changing its size. */
.workspace-tabs-strip :deep(.p-tab-active) {
    font-weight: 700;
}
</style>
