<script setup lang="ts">
import arches from "arches";
import { inject, onMounted, ref } from "vue";
import { useGettext } from "vue3-gettext";

import Message from "primevue/message";
import Panel from "primevue/panel";

import { fetchNodeTileData } from "@/arches_provenance/EditableReport/api.ts";
import LabeledNodeValues from "@/arches_provenance/EditableReport/components/LabeledNodeValues.vue";

import type { Ref } from "vue";
import type {
    NodePresentationLookup,
    NodeValueDisplayDataLookup,
    SectionContent,
} from "@/arches_provenance/EditableReport/types";

const resourceInstanceId = inject("resourceInstanceId") as string;

const props = defineProps<{
    component: SectionContent;
}>();

const nodePresentationLookup = inject(
    "nodePresentationLookup",
) as NodePresentationLookup;
const { $gettext } = useGettext();

const hasLoadingError = ref(false);
const displayDataByAlias: Ref<NodeValueDisplayDataLookup> = ref({});

async function fetchData() {
    try {
        displayDataByAlias.value = await fetchNodeTileData(
            resourceInstanceId,
            props.component.config.nodes,
        );
        hasLoadingError.value = false;
    } catch {
        hasLoadingError.value = true;
    }
}

onMounted(fetchData);
</script>

<template>
    <Panel>
        <div class="data-container">
            <Message
                v-if="hasLoadingError"
                severity="error"
                style="height: 3rem; width: fit-content"
            >
                {{ $gettext("Unable to fetch resource") }}
            </Message>
            <template v-else-if="displayDataByAlias && nodePresentationLookup">
                <LabeledNodeValues
                    v-for="nodeAlias in props.component.config.nodes"
                    :key="nodeAlias"
                    :node-presentation="nodePresentationLookup[nodeAlias]"
                    :display-data="displayDataByAlias[nodeAlias]"
                />
            </template>
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
    max-width: 100%;
    height: auto;
    object-fit: contain;
    align-self: end;
}
</style>
