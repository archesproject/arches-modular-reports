<script setup lang="ts">
import arches from "arches";
import { computed, inject, onMounted, ref } from "vue";
import { useGettext } from "vue3-gettext";

import Message from "primevue/message";
import Panel from "primevue/panel";

import { fetchNodeTileData } from "@/arches_modular_reports/ModularReport/api.ts";
import { RESOURCE_LIMIT_FOR_HEADER } from "@/arches_modular_reports/constants.ts";
import LabeledNodeValues from "@/arches_modular_reports/ModularReport/components/LabeledNodeValues.vue";

import type { Ref } from "vue";
import type {
    NodePresentationLookup,
    NodeValueDisplayDataLookup,
    SectionContent,
} from "@/arches_modular_reports/ModularReport/types";

const resourceInstanceId = inject("resourceInstanceId") as string;

const props = defineProps<{
    component: SectionContent;
}>();

const nodePresentationLookup = inject("nodePresentationLookup") as Ref<
    NodePresentationLookup | undefined
>;
const { $gettext } = useGettext();

const isLoading = ref(true);
const hasLoadingError = ref(false);
const displayDataByAlias: Ref<NodeValueDisplayDataLookup | null> = ref(null);
const imageNodeData = ref(null);

interface ImageTileData {
    display_value: string;
    links: { alt_text: string; link: string }[];
}

const firstImageTileData = computed(() => {
    const data =
        imageNodeData.value?.[props.component.config.image_node_alias]?.[0];
    return data as ImageTileData | undefined;
});

const imageUrl = computed(() => {
    if (isLoading.value) {
        return "";
    }
    if (!firstImageTileData.value) {
        return arches.urls.media + "img/photo_missing.png";
    }
    return firstImageTileData.value.links[0].link;
});

const imageAltText = computed(() => {
    if (isLoading.value) {
        return "";
    }
    if (!firstImageTileData.value) {
        return $gettext("Image not available");
    }
    return firstImageTileData.value.links[0].alt_text;
});

function bestWidgetLabel(nodeAlias: string) {
    return (
        props.component.config.custom_labels?.[nodeAlias] ??
        nodePresentationLookup.value?.[nodeAlias].widget_label ??
        nodeAlias
    );
}

async function fetchData() {
    isLoading.value = true;
    try {
        displayDataByAlias.value = await fetchNodeTileData(
            resourceInstanceId,
            props.component.config.node_aliases,
            RESOURCE_LIMIT_FOR_HEADER,
        );
        if (props.component.config.image_node_alias) {
            imageNodeData.value = await fetchNodeTileData(
                resourceInstanceId,
                [props.component.config.image_node_alias],
                1,
            );
        }
        hasLoadingError.value = false;
    } catch {
        hasLoadingError.value = true;
    } finally {
        isLoading.value = false;
    }
}

onMounted(fetchData);
</script>

<template>
    <Panel style="border: 0; border-radius: 0">
        <div class="data-container">
            <Message
                v-if="hasLoadingError"
                severity="error"
                style="height: 3rem; width: fit-content"
            >
                {{ $gettext("Unable to fetch resource") }}
            </Message>
            <template v-else-if="displayDataByAlias">
                <LabeledNodeValues
                    v-for="nodeAlias in props.component.config.node_aliases"
                    :key="nodeAlias"
                    :node-alias="nodeAlias"
                    :widget-label="bestWidgetLabel(nodeAlias)"
                    :display-data="displayDataByAlias[nodeAlias]"
                />
            </template>
        </div>
        <div
            v-if="imageNodeData"
            class="image-container"
        >
            <img
                :src="imageUrl"
                :alt="imageAltText"
            />
        </div>
    </Panel>
</template>

<style scoped>
:deep(.p-panel-header) {
    padding-top: 6px;
    padding-bottom: 6px;
}

:deep(.p-panel-content) {
    display: flex;
    justify-content: space-between;
    width: 100%;
    gap: 1rem;
}

.data-container {
    width: 100%;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(18rem, 1fr));
    gap: 2rem;
}

.image-container {
    max-width: 18rem;
}

img {
    width: 100%;
    height: auto;
    object-fit: contain;
    align-self: end;
}

@media print {
    .data-container {
        grid-template-columns: unset;
        padding: 2rem;
    }
}
</style>
