<script setup lang="ts">
import { provide, ref, watchEffect } from "vue";
import { useGettext } from "vue3-gettext";

import Message from "openvue/message";

import { fetchReportConfig } from "@/arches_modular_reports/ModularReport/api.ts";
import { importComponents } from "@/arches_modular_reports/ModularReport/utils.ts";
import { toError } from "@/arches_modular_reports/utils.ts";

import type {
    ComponentLookup,
    NamedSection,
} from "@/arches_modular_reports/ModularReport/types.ts";

const {
    graphSlug,
    resourceInstanceId = "",
    reportConfigSlug = "default",
} = defineProps<{
    graphSlug: string;
    resourceInstanceId?: string;
    reportConfigSlug?: string;
}>();

provide("graphSlug", graphSlug);
provide("resourceInstanceId", resourceInstanceId);

const { $gettext } = useGettext();

const componentLookup: ComponentLookup = {};
const config = ref<NamedSection | null>(null);
const fetchError = ref<Error | null>(null);

watchEffect(async () => {
    if (!resourceInstanceId) {
        return;
    }
    try {
        const reportConfig = await fetchReportConfig(
            resourceInstanceId,
            reportConfigSlug,
        );
        await importComponents([reportConfig], componentLookup);
        config.value = reportConfig;
    } catch (error) {
        fetchError.value = toError(error);
    }
});
</script>

<template>
    <div class="modular-report">
        <Message
            v-if="!resourceInstanceId"
            severity="info"
        >
            <span>
                {{ $gettext("Open a resource to see its report.") }}
            </span>
        </Message>
        <Message
            v-else-if="fetchError"
            severity="error"
        >
            <span>
                {{
                    $gettext("Unable to load the report: %{message}", {
                        message: fetchError.message,
                    })
                }}
            </span>
        </Message>
        <template v-else-if="config">
            <component
                :is="componentLookup[sectionContent.component].component"
                v-for="(sectionContent, sectionIndex) in config.components"
                :key="sectionIndex"
                :component="sectionContent"
                :resource-instance-id="resourceInstanceId"
            />
        </template>
    </div>
</template>

<style scoped>
.modular-report {
    height: 100%;
}
</style>
