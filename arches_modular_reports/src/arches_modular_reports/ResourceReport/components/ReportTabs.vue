<script setup lang="ts">
import Tab from "openvue/tab";
import TabList from "openvue/tablist";
import TabPanel from "openvue/tabpanel";
import TabPanels from "openvue/tabpanels";
import Tabs from "openvue/tabs";

import { loadComponent } from "@/arches_modular_reports/ModularReport/utils.ts";
import { useTabbedComponents } from "@/arches_modular_reports/ResourceReport/composables/useTabbedComponents.ts";

import type {
    ComponentNode,
    ReportTabsConfig,
} from "@/arches_modular_reports/ResourceReport/types.ts";

const { component } = defineProps<{
    component: ComponentNode<ReportTabsConfig>;
}>();

const { tabs, activeTabIndex } = useTabbedComponents(
    () => component.config.components ?? [],
);
</script>

<template>
    <Tabs
        v-model:value="activeTabIndex"
        class="report-tabs"
        :lazy="true"
        :show-navigators="false"
    >
        <TabList
            v-if="tabs.length > 1"
            class="report-tabs-list"
        >
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
                :value="tabIndex"
            >
                <div class="report-tabs-panel">
                    <component
                        :is="loadComponent(tab.node.component)"
                        :component="tab.node"
                    />
                </div>
            </TabPanel>
        </TabPanels>
    </Tabs>
</template>

<style scoped>
.report-tabs {
    --p-tabs-tablist-background: var(--resource-report-panel-background);
    --p-tabs-tab-padding: 0.8rem 1.4rem;
    --p-tabs-tab-font-weight: 500;
    --p-tabs-tab-hover-color: var(--p-text-color);
    --p-tabs-active-bar-height: 0.2rem;
    --p-tabs-tabpanel-padding: 1.6rem;
}

.report-tabs-list {
    position: sticky;
    inset-block-start: 0;
    z-index: 1;
}

.report-tabs-list :deep(.p-tablist-tab-list) {
    padding-inline: 1.6rem;
}

.report-tabs-list :deep(.p-tab) {
    font-size: 1.3rem;
    line-height: 1.4;
}

.report-tabs-list :deep(.p-tab-active) {
    font-weight: 600;
}

.report-tabs-panel {
    max-inline-size: 120rem;
    line-height: 1.4;
}
</style>
