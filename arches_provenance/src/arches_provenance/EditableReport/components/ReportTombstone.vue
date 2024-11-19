<script setup lang="ts">
import arches from "arches";
import { inject } from "vue";
import { useGettext } from "vue3-gettext";

import Panel from "primevue/panel";

import { findNodeValue } from "@/arches_provenance/EditableReport/utils.ts";

import type {
    NodePresentationLookup,
    SectionContent,
    Tile,
} from "@/arches_provenance/EditableReport/types";

const resource = inject("resource") as { resource: Tile };
const nodePresentationLookup = inject(
    "nodePresentationLookup",
) as NodePresentationLookup;
const { $gettext } = useGettext();
</script>

<template>
    <Panel>
        <div
            v-if="resource && nodePresentationLookup"
            class="data-container"
        >
            <!-- Eventually this will become its own component -->
            <div
                v-for="nodeAlias in ($attrs.content as SectionContent).config
                    .nodes"
                :key="nodeAlias"
                class="datatype-widget"
            >
                <span>
                    <strong>{{
                        nodePresentationLookup[nodeAlias].widget_label
                    }}</strong>
                </span>
                <span class="node-value">
                    {{ findNodeValue(resource, nodeAlias) }}
                </span>
            </div>
        </div>
        <div class="image-container">
            <img
                :src="arches.urls.media + 'img/photo_missing.png'"
                :alt="$gettext('Image not available')"
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
}

.data-container {
    width: 75%;
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 30px;
}

.datatype-widget {
    display: flex;
    gap: 10px;
}

.datatype-widget span.node-value {
    overflow-wrap: anywhere;
}

.image-container {
    width: 15%;
    height: 15%;
}

img {
    width: 100%;
    height: 100%;
    object-fit: contain;
}
</style>
