<script setup lang="ts">
import { onMounted, ref } from "vue";

import Tab from "primevue/tab";
import Tabs from "primevue/tabs";
import TabList from "primevue/tablist";
import TabPanel from "primevue/tabpanel";
import TabPanels from "primevue/tabpanels";

import {
    importComponents,
    uniqueId,
} from "@/arches_provenance/EditableReport/utils.ts";

import type {
    ComponentLookup,
    NamedSection,
    SectionContent,
} from "@/arches_provenance/EditableReport/types";

const componentLookup: ComponentLookup = {};

const { component, resourceInstanceId } = defineProps<{
    component: SectionContent;
    resourceInstanceId: string;
}>();

const activeTab = ref<string>(component.config.tabs[0].name);

onMounted(() => {
    importComponents(component.config.tabs, componentLookup);

    component.config.tabs.forEach((tab: NamedSection) => {
        tab.components.forEach((child: SectionContent) => {
            child.config.id = uniqueId(child);
        });
    });
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
                <div v-if="activeTab === tab.name">
                    <component
                        :is="componentLookup[tabComponent.component]"
                        v-for="tabComponent in tab.components"
                        :key="tabComponent.config.id"
                        :component="tabComponent"
                        :resource-instance-id="resourceInstanceId"
                    />
                </div>
            </TabPanel>
        </TabPanels>
    </Tabs>
</template>
