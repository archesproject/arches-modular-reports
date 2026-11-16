<script setup lang="ts">
import { computed } from "vue";

import GenericWidget from "@/arches_vue_components/generics/GenericWidget/GenericWidget.vue";
import LanguageName from "@/arches_modular_reports/ResourceReport/components/LanguageName.vue";

import { VIEW } from "@/arches_vue_components/widgets/constants.ts";
import { useReportData } from "@/arches_modular_reports/ResourceReport/composables/useReportData.ts";
import {
    hasOtherLanguages,
    localizedTexts,
} from "@/arches_modular_reports/ResourceReport/utils/localized-text.ts";

import type {
    AliasedNodeData,
    CardXNodeXWidgetData,
} from "@/arches_vue_components/types.ts";
import type { LocalizedText } from "@/arches_modular_reports/ResourceReport/utils/localized-text.ts";

const { nodeData, widget } = defineProps<{
    nodeData: AliasedNodeData;
    widget: CardXNodeXWidgetData;
}>();

const reportData = useReportData();

const activeLanguage = computed(() => reportData.value.context.language);

const texts = computed(() => localizedTexts(nodeData, activeLanguage.value));

// Only a value with text in another language needs naming; one in the active
// language alone reads as it always has.
const isMultilingual = computed(() =>
    hasOtherLanguages(texts.value, activeLanguage.value),
);

function languageName(languageCode: string): string {
    return reportData.value.context.languages?.[languageCode] ?? languageCode;
}

// The widget renders its display value, so each language gets one of its own.
function nodeDataIn(text: LocalizedText): AliasedNodeData {
    return {
        ...nodeData,
        display_value: text.value,
        node_value: {
            [text.languageCode]: {
                value: text.value,
                direction: text.direction,
            },
        },
    };
}
</script>

<template>
    <div
        v-if="isMultilingual"
        class="node-value-languages"
    >
        <div
            v-for="text in texts"
            :key="text.languageCode"
            class="node-value-language"
        >
            <div
                class="node-value-language-text"
                :lang="text.languageCode"
                :dir="text.direction"
            >
                <GenericWidget
                    :aliased-node-data="nodeDataIn(text)"
                    :card-x-node-x-widget-data="widget"
                    :graph-slug="reportData.context.graph.slug"
                    :mode="VIEW"
                    :node-alias="widget.node.alias"
                    :should-show-label="false"
                />
            </div>
            <LanguageName
                v-if="text.languageCode !== activeLanguage"
                :name="languageName(text.languageCode)"
            />
        </div>
    </div>
    <GenericWidget
        v-else
        :aliased-node-data="nodeData"
        :card-x-node-x-widget-data="widget"
        :graph-slug="reportData.context.graph.slug"
        :mode="VIEW"
        :node-alias="widget.node.alias"
        :should-show-label="false"
    />
</template>

<style scoped>
.node-value-languages {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
}

.node-value-language {
    display: flex;
    align-items: baseline;
    gap: 0.6rem;
}

.node-value-language-text {
    min-inline-size: 0;
}
</style>
