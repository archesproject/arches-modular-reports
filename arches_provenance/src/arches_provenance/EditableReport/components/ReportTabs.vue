<script setup lang="ts">
import { inject } from "vue";

import Tab from "primevue/tab";
import Tabs from "primevue/tabs";
import TabList from "primevue/tablist";
import TabPanel from "primevue/tabpanel";
import TabPanels from "primevue/tabpanels";

import type { SectionContent } from "@/arches_provenance/EditableReport/types";

const { component, resourceInstanceId } = defineProps<{
    component: SectionContent;
    resourceInstanceId: string;
}>();

const componentLookup = inject("components") as { [key: string]: string };
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
                    :key="tabComponent.component"
                    :component="tabComponent"
                    :resource-instance-id
                />
            </TabPanel>
        </TabPanels>
    </Tabs>
</template>
