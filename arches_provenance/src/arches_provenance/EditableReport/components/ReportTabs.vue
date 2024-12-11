<script setup lang="ts">
import { onMounted } from "vue";

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
    SectionContent,
} from "@/arches_provenance/EditableReport/types";

const componentLookup: ComponentLookup = {};

const { component, resourceInstanceId } = defineProps<{
    component: SectionContent;
    resourceInstanceId: string;
}>();

onMounted(() => importComponents(component.config.tabs, componentLookup));
</script>

<template>
    <Tabs :value="component.config.tabs[0].name">
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
                <!--Consider <keep-alive> if future refactors cause these to be rerendered.-->
                <component
                    :is="componentLookup[tabComponent.component]"
                    v-for="tabComponent in tab.components"
                    :key="uniqueId(tabComponent)"
                    :component="tabComponent"
                    :resource-instance-id
                />
            </TabPanel>
        </TabPanels>
    </Tabs>
</template>
