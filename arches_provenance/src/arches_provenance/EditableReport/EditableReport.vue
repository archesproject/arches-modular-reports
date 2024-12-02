<script setup lang="ts">
import {
    defineAsyncComponent,
    onMounted,
    provide,
    ref,
    useTemplateRef,
} from "vue";
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
const sectionContainerRef = useTemplateRef("section-container");
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
    const reportContainer = sectionContainerRef.value!.closest(
        ".resource-report-abstract-container",
    );
    const resourceId = reportContainer!.getAttribute("data-resourceid")!;
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
    <div
        ref="section-container"
        class="section-container"
    >
        <h2>{{ config.name }}</h2>
        <!--Consider <keep-alive> if future refactors cause these to be rerendered.-->
        <component
            :is="componentLookup[component.component]"
            v-for="component in config.components"
            :key="component.component"
            :component
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
