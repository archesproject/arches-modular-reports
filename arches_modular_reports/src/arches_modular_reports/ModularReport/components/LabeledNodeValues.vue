<script setup lang="ts">
import { computed, inject, ref } from "vue";

import Button from "primevue/button";

import { RESOURCE_LIMIT_FOR_HEADER } from "@/arches_modular_reports/constants.ts";
import {
    truncateDisplayData,
    formatNumber,
} from "@/arches_modular_reports/ModularReport/utils.ts";

import type { Ref } from "vue";
import type {
    NodeValueDisplayData,
    NodePresentationLookup,
    LanguageSettings,
} from "@/arches_modular_reports/ModularReport/types";

const props = defineProps<{
    widgetLabel: string;
    displayData: NodeValueDisplayData[];
    nodeAlias: string;
}>();

const nodePresentationLookup = inject("nodePresentationLookup") as Ref<
    NodePresentationLookup | undefined
>;
const languageSettings = inject(
    "languageSettings",
    ref({ ACTIVE_LANGUAGE: "en", ACTIVE_LANGUAGE_DIRECTION: "ltr" }),
) as Ref<LanguageSettings>;
const truncatedDisplayData = computed(() => {
    return truncateDisplayData(props.displayData, RESOURCE_LIMIT_FOR_HEADER);
});

function formatValue(value: string): string {
    const nodePresentation = nodePresentationLookup.value?.[props.nodeAlias];
    if (nodePresentation?.is_numeric && nodePresentation?.number_format) {
        return formatNumber(
            value,
            nodePresentation.number_format,
            languageSettings,
        );
    }
    return value;
}
</script>

<template>
    <div class="node-container">
        <strong>{{ widgetLabel }}</strong>
        <div class="node-values-container">
            <template
                v-for="nodeValueDisplayData in truncatedDisplayData"
                :key="nodeValueDisplayData.display_values"
            >
                <template v-if="nodeValueDisplayData.links.length">
                    <div
                        v-for="link in nodeValueDisplayData.links"
                        :key="JSON.stringify(link)"
                        class="node-value"
                    >
                        <Button
                            as="a"
                            class="node-value"
                            target="_blank"
                            variant="link"
                            :label="link.label"
                            :href="link.link"
                        >
                        </Button>
                    </div>
                </template>
                <template v-else>
                    <div
                        v-for="innerValue in nodeValueDisplayData.display_values"
                        :key="innerValue"
                        class="node-value"
                    >
                        {{ formatValue(innerValue) }}
                    </div>
                </template>
            </template>
        </div>
    </div>
</template>

<style scoped>
.node-container {
    display: flex;
    flex-direction: column;
    max-height: 18rem;
}

.node-values-container {
    height: 100%;
    overflow: auto;
}

.node-value {
    align-items: unset;
    overflow-wrap: anywhere;
}

.p-button-link {
    font-size: inherit;
    padding: 0;
    align-items: start;
    overflow: unset;
}
</style>
