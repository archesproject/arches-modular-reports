<script setup lang="ts">
import { defineAsyncComponent, onMounted, provide, ref } from "vue";
import { useGettext } from "vue3-gettext";

import Toast from "primevue/toast";
import { useToast } from "primevue/usetoast";

import {
    fetchNodePresentation,
    fetchReportConfig,
    fetchResource,
} from "@/arches_provenance/EditableReport/api.ts";
import { DEFAULT_ERROR_TOAST_LIFE } from "@/arches_provenance/constants.ts";

import type { Ref } from "vue";
import type {
    NamedSection,
    NodePresentationLookup,
    SectionContent,
    Tile,
} from "@/arches_provenance/EditableReport/types";

const toast = useToast();
const { $gettext } = useGettext();
const resourceInstanceId = window.location.href.split("/").reverse()[0];
const componentLookup: { [key: string]: string } = {};

const resource: Ref<{ resource: Tile } | null> = ref(null);
provide("resource", resource);

const nodePresentationLookup: Ref<NodePresentationLookup | null> = ref(null);
provide("nodePresentationLookup", nodePresentationLookup);

const config: Ref<NamedSection> = ref({
    name: $gettext("Loading data"),
    components: [{ component: "", config: {} }],
});

onMounted(async () => {
    try {
        const promises = await Promise.all([
            fetchResource(resourceInstanceId),
            fetchNodePresentation(resourceInstanceId),
            fetchReportConfig(resourceInstanceId),
        ]);
        resource.value = promises[0];
        nodePresentationLookup.value = promises[1];
        config.value = promises[2];
    } catch (error) {
        toast.add({
            severity: "error",
            life: DEFAULT_ERROR_TOAST_LIFE,
            summary: $gettext("Unable to fetch resource"),
            detail: (error as Error).message ?? error,
        });
        return;
    }
    config.value.components.forEach((component: SectionContent) => {
        componentLookup[component.component] = defineAsyncComponent(
            () =>
                import(
                    `@/arches_provenance/EditableReport/components/${component.component}.vue`
                ),
        );
    });
});
</script>

<template>
    <div class="section-container">
        <h2>{{ config.name }}</h2>
        <!--Consider <keep-alive> if future refactors cause these to be rerendered.-->
        <component
            :is="componentLookup[component.component]"
            v-for="component in config.components"
            :key="component.component"
            :component
            :resource-instance-id
        />
    </div>
    <Toast
        :pt="{
            messageIcon: { style: { marginTop: 'var(--p-toast-content-gap)' } },
        }"
    />
</template>

<style scoped>
.section-container {
    gap: 2rem;
    height: calc(100vh - 50px);
    width: calc(100vw - 50px);
}
</style>
