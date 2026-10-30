<script setup lang="ts">
import { computed } from "vue";

import Tab from "openvue/tab";
import TabList from "openvue/tablist";
import Tabs from "openvue/tabs";

import { loadComponent } from "@/arches_modular_reports/ModularReport/utils.ts";
import { useTabbedComponents } from "@/arches_modular_reports/ResourceReport/composables/useTabbedComponents.ts";

import type {
    ComponentNode,
    WorkspaceTabsConfig,
} from "@/arches_modular_reports/ResourceReport/types.ts";

const WORKSPACE_STRIP_TOKENS = {
    tablist: { background: "{resource.report.strip.background}" },
    tab: { padding: "0.9rem 1.6rem", fontWeight: "500" },
};

const { component } = defineProps<{
    component: ComponentNode<WorkspaceTabsConfig>;
}>();

const { tabs, activeTabIndex, activeTab } = useTabbedComponents(
    () => component.config.components ?? [],
);

const bannerNodes = computed(() => component.config.banner ?? []);
</script>

<template>
    <div class="workspace-tabs">
        <Tabs
            v-if="tabs.length > 1"
            v-model:value="activeTabIndex"
            class="workspace-tabs-strip"
            :show-navigators="false"
            :dt="WORKSPACE_STRIP_TOKENS"
        >
            <TabList>
                <Tab
                    v-for="(tab, tabIndex) in tabs"
                    :key="tabIndex"
                    :value="tabIndex"
                >
                    <span>{{ tab.label }}</span>
                </Tab>
            </TabList>
        </Tabs>
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

.workspace-tabs-strip :deep(.p-tab) {
    font-size: 1.3rem;
    letter-spacing: 0.08rem;
    text-transform: uppercase;
}

.workspace-tabs-caption {
    margin: 0;
    padding-block: 0.5rem;
    padding-inline: 1.6rem;
    border-block-end: 0.1rem solid var(--p-content-border-color);
    background: var(--p-resource-report-caption-background);
    color: var(--p-text-muted-color);
    font-size: 1.15rem;
}
</style>
