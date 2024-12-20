<script setup lang="ts">
import { inject, onMounted, provide, ref } from "vue";
import { useGettext } from "vue3-gettext";

import Toast from "primevue/toast";
import { useToast } from "primevue/usetoast";

import {
    fetchNodePresentation,
    fetchReportConfig,
    fetchResource,
} from "@/arches_provenance/EditableReport/api.ts";
import { DEFAULT_ERROR_TOAST_LIFE } from "@/arches_provenance/constants.ts";
import {
    importComponents,
    uniqueId,
} from "@/arches_provenance/EditableReport/utils.ts";

import type { Ref } from "vue";
import type {
    ComponentLookup,
    NamedSection,
    NodePresentationLookup,
    Tile,
} from "@/arches_provenance/EditableReport/types";

const toast = useToast();
const { $gettext } = useGettext();
const componentLookup: ComponentLookup = {};

const resourceInstanceId = inject("resourceInstanceId") as string;
const resource: Ref<{ resource: Tile } | null> = ref(null);
provide("resource", resource);

const nodePresentationLookup: Ref<NodePresentationLookup | null> = ref(null);
provide("nodePresentationLookup", nodePresentationLookup);

const config: Ref<NamedSection> = ref({
    name: $gettext("Loading data"),
    components: [{ component: "", config: {} }],
});

onMounted(async () => {
    if (!resourceInstanceId) {
        return;
    }
    try {
        await Promise.all([
            fetchResource(resourceInstanceId).then(
                (data) => (resource.value = data),
            ),
            fetchNodePresentation(resourceInstanceId).then(
                (data) => (nodePresentationLookup.value = data),
            ),
            fetchReportConfig(resourceInstanceId).then((data) => {
                importComponents([data], componentLookup);
                config.value = data;
            }),
        ]);
    } catch (error) {
        toast.add({
            severity: "error",
            life: DEFAULT_ERROR_TOAST_LIFE,
            summary: $gettext("Unable to fetch resource"),
            detail: (error as Error).message ?? error,
        });
        return;
    }
});
</script>

<template>
    <div class="section-container">
        <h2>{{ config.name }}</h2>
        <!--Consider <keep-alive> if future refactors cause these to be rerendered.-->
        <component
            :is="componentLookup[component.component]"
            v-for="component in config.components"
            :key="uniqueId(component)"
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
:deep(.p-button-label),
:deep(.pi) {
    font-size: 1.4rem;
}
</style>
