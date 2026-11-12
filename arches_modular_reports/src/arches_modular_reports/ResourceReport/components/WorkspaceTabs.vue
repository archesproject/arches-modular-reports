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
                <!-- The caption is optional: a workspace whose config omits
                     `description`, or leaves it blank in every language, has none. -->
                <p
                    v-if="activeTab?.description"
                    class="workspace-tabs-caption"
                >
                    {{ activeTab.description }}
                </p>
                <component
                    :is="loadComponent(bannerNode.component)"
                    v-for="(bannerNode, bannerIndex) in bannerNodes"
                    :key="bannerIndex"
                    :component="bannerNode"
                />
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

/* Tab strip on the left, export links right-justified, on one bar. */
.workspace-tabs-bar {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 1.6rem;
    block-size: var(--resource-report-bar-block-size);
    padding-inline-end: 1.6rem;
    border-block-end: 0.1rem solid var(--resource-report-bar-border-color);
    background: var(--resource-report-bar-background);
}

.workspace-tabs-bar .workspace-tabs-exports {
    flex-shrink: 0;
}

.workspace-tabs-strip {
    flex: 1;
    min-inline-size: 0;
    --p-tabs-tablist-background: var(--resource-report-bar-background);
    --p-tabs-tablist-border-color: var(--resource-report-bar-border-color);
    --p-tabs-tab-padding: 0 1rem;
    --p-tabs-tab-font-weight: 500;
    --p-tabs-tab-border-color: transparent;
    --p-tabs-tab-hover-border-color: transparent;
    --p-tabs-active-bar-height: 0.2rem;
}

.workspace-tabs-strip :deep(.p-tablist-tab-list) {
    padding-inline: 0.4rem;
    /* The bar draws the bottom border across its full width. */
    border-block-end: none;
}

/* Tabs fill the bar (less its bottom border) so the active bar sits on the
   bar's bottom edge. */
.workspace-tabs-strip :deep(.p-tab) {
    block-size: calc(var(--resource-report-bar-block-size) - 0.1rem);
    font-size: 1.3rem;
    letter-spacing: 0.08rem;
    text-transform: uppercase;
    font-weight: 600;
}

.workspace-tabs-caption {
    margin: 0;
    padding-block: 0.5rem;
    padding-inline: 1.6rem;
    border-block-end: 0.1rem solid var(--p-content-border-color);
    background: var(--resource-report-muted-background);
    color: var(--p-text-muted-color);
    font-size: 1.15rem;
}
</style>
