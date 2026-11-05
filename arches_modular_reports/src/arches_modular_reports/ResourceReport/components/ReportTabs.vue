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

const REPORT_TABS_TOKENS = {
    tablist: { background: "var(--resource-report-subtabs-background)" },
    tab: {
        padding: "0.8rem 1.4rem",
        fontWeight: "500",
        borderColor: "transparent",
        hoverBorderColor: "transparent",
        activeBorderColor: "transparent",
        color: "{text.muted.color}",
        hoverColor: "{text.color}",
    },
    activeBar: { height: "0.2rem" },
    tabpanel: { padding: "1.6rem" },
};

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
        :lazy="true"
        :show-navigators="false"
        :dt="REPORT_TABS_TOKENS"
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
