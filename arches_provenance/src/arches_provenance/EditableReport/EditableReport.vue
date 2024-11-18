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
} from "@/arches_provenance/EditableReport/types";

const toast = useToast();
const { $gettext } = useGettext();
const resourceId = window.location.href.split("/").reverse()[0];
const componentLookup: { [key: string]: string } = {};

const resource: Ref<{ [key: string]: any } | null> = ref(null);
provide("resource", resource);

const nodePresentationLookup: Ref<NodePresentationLookup | null> = ref(null);
provide("nodePresentationLookup", nodePresentationLookup);

const config: Ref<NamedSection> = ref({
    name: $gettext("Loading data"),
    content: [{ component: "", config: {} }],
});

onMounted(async () => {
    try {
        const promises = await Promise.all([
            fetchResource(resourceId),
            fetchNodePresentation(resourceId),
            fetchReportConfig(resourceId),
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
    config.value.content.forEach((content: SectionContent) => {
        componentLookup[content.component] = defineAsyncComponent(
            () =>
                import(
                    `@/arches_provenance/EditableReport/components/${content.component}.vue`
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
            :is="componentLookup[content.component]"
            v-for="content in config.content"
            :key="content.component"
            :content
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
}
</style>
