<script setup lang="ts">
import arches from "arches";
import { inject } from "vue";
import { useGettext } from "vue3-gettext";

import Panel from "primevue/panel";

import { findNodeValue } from "@/arches_provenance/utils.ts";

import type { SectionContent } from "@/arches_provenance/EditableReport/types";

const resource = inject("resource");
const { $gettext } = useGettext();
</script>

<template>
    <Panel>
        <div
            v-if="resource"
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
                    <strong>{{ nodeAlias }}</strong>
                </span>
                <span>
                    {{ findNodeValue(resource, nodeAlias) }}
                </span>
            </div>
        </div>
        <img
            :src="arches.urls.media + 'img/photo_missing.png'"
            :alt="$gettext('Image not available')"
        />
    </Panel>
</template>

<style scoped>
:deep(.p-panel-content) {
    display: flex;
    justify-content: space-between;
    width: 100%;
}

.data-container {
    width: 75%;
    display: grid;
    grid-template-columns: repeat(4, 1fr);
}

.datatype-widget {
    display: flex;
    gap: 1rem;
}

img {
    width: 15%;
}
</style>
