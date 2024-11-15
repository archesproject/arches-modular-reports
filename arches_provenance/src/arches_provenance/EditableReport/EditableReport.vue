<script setup lang="ts">
import { defineAsyncComponent, onMounted, ref } from "vue";
import { useGettext } from "vue3-gettext";

import Toast from "primevue/toast";
import { useToast } from "primevue/usetoast";

import { fetchReportConfig } from "@/arches_provenance/EditableReport/api.ts";
import { DEFAULT_ERROR_TOAST_LIFE } from "@/arches_provenance/constants.ts";

import type {
    NamedSection,
    SectionContent,
} from "@/arches_provenance/EditableReport/types";

const toast = useToast();
const { $gettext } = useGettext();
const resourceId = window.location.href.split("/").reverse()[0];
const componentLookup = {};

const config: NamedSection = ref({
    name: "Loading...",
    content: [{ component: "", config: {} }],
});

onMounted(async () => {
    try {
        config.value = await fetchReportConfig(resourceId);
    } catch (error) {
        toast.add({
            severity: "error",
            life: DEFAULT_ERROR_TOAST_LIFE,
            summary: $gettext("Unable to fetch report config"),
            detail: error.message ?? error,
        });
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
