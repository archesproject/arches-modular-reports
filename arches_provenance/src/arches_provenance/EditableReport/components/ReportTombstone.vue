<script setup lang="ts">
import arches from "arches";
import { inject } from "vue";
import { useGettext } from "vue3-gettext";

import Panel from "primevue/panel";

import { findNodeValue } from "@/arches_provenance/EditableReport/utils.ts";
import GenericDatatype from "@/arches_provenance/DatatypeWidgets/components/GenericDatatype.vue";

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
            <GenericDatatype
                v-for="nodeAlias in ($attrs.content as SectionContent).config
                    .nodes"
                :key="nodeAlias"
                :node-presentation="nodePresentationLookup[nodeAlias]"
                :tile-value="findNodeValue(resource, nodeAlias)"
            />
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
