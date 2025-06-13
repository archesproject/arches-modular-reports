<script setup lang="ts">
import { inject, onMounted, provide, ref } from "vue";
import { useGettext } from "vue3-gettext";

import Toast from "primevue/toast";
import { useToast } from "primevue/usetoast";

import {
    fetchNodePresentation,
    fetchReportConfig,
    fetchUserResourcePermissions,
} from "@/arches_modular_reports/ModularReport/api.ts";
import { DEFAULT_ERROR_TOAST_LIFE } from "@/arches_modular_reports/constants.ts";
import {
    importComponents,
    uniqueId,
} from "@/arches_modular_reports/ModularReport/utils.ts";

import type { Ref } from "vue";
import type {
    ComponentLookup,
    NamedSection,
    NodePresentationLookup,
} from "@/arches_modular_reports/ModularReport/types";

const toast = useToast();
const { $gettext } = useGettext();
const componentLookup: ComponentLookup = {};

const resourceInstanceId = inject("resourceInstanceId") as string;

const nodePresentationLookup: Ref<NodePresentationLookup | undefined> = ref();
provide("nodePresentationLookup", nodePresentationLookup);

const userCanEditResourceInstance = ref(false);
provide("userCanEditResourceInstance", userCanEditResourceInstance);

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
            fetchNodePresentation(resourceInstanceId).then(
                (data) => (nodePresentationLookup.value = data),
            ),
            fetchUserResourcePermissions(resourceInstanceId).then((data) => {
                userCanEditResourceInstance.value = data.edit;
            }),
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
    <div style="position: absolute; width: 100%">
        <component
            :is="componentLookup[component.component]"
            v-for="component in config.components"
            :key="uniqueId(component)"
            :component
            :resource-instance-id
        />
    </div>

    <Toast />
</template>
