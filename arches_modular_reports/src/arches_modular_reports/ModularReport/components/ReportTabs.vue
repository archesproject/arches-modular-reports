<script setup lang="ts">
import { ref, watch, watchEffect } from "vue";

import Tab from "primevue/tab";
import Tabs from "primevue/tabs";
import TabList from "primevue/tablist";
import TabPanel from "primevue/tabpanel";
import TabPanels from "primevue/tabpanels";

import {
    importComponents,
    uniqueId,
} from "@/arches_modular_reports/ModularReport/utils.ts";

import type {
    ComponentLookup,
    NamedSection,
    SectionContent,
} from "@/arches_modular_reports/ModularReport/types";

const componentLookup: ComponentLookup = {};

const { component, resourceInstanceId } = defineProps<{
    component: SectionContent;
    resourceInstanceId: string;
}>();

const activeTab = ref(component.config.tabs[0].name);
const visitedTabs = ref<Set<string>>(new Set([activeTab.value]));

watchEffect(() => {
    importComponents(component.config.tabs, componentLookup);

    component.config.tabs.forEach((tab: NamedSection) => {
        tab.components.forEach((child: SectionContent) => {
            child.config.id = uniqueId(child);
        });
    });
});

watch(activeTab, (tab) => {
    visitedTabs.value.add(tab);
});
</script>

<template>
    <Tabs v-model:value="activeTab">
        <TabList>
            <Tab
                v-for="tab in component.config.tabs"
                :key="tab.name"
                :value="tab.name"
            >
                {{ tab.name }}
            </Tab>
        </TabList>
        <TabPanels>
            <TabPanel
                v-for="tab in component.config.tabs"
                :key="tab.name"
                :value="tab.name"
            >
                <template v-if="visitedTabs.has(tab.name)">
                    <component
                        :is="componentLookup[tabComponent.component]?.component"
                        v-for="tabComponent in tab.components"
                        :key="componentLookup[tabComponent.component]?.key"
                        :component="tabComponent"
                        :resource-instance-id="resourceInstanceId"
                    />
                </template>
            </TabPanel>
        </TabPanels>
    </Tabs>
</template>
