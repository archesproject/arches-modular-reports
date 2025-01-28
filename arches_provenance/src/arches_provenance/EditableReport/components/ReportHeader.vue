<script setup lang="ts">
import { computed, inject, onMounted, ref } from "vue";
import { useGettext } from "vue3-gettext";

import Message from "primevue/message";
import Panel from "primevue/panel";

import { fetchNodeTileData } from "@/arches_provenance/EditableReport/api.ts";

import type { Ref } from "vue";
import type {
    NodePresentationLookup,
    NodeValueDisplayDataLookup,
    SectionContent,
} from "@/arches_provenance/EditableReport/types";

const resourceInstanceId = inject("resourceInstanceId") as string;

const props = defineProps<{ component: SectionContent }>();

const nodePresentationLookup = inject("nodePresentationLookup") as Ref<
    NodePresentationLookup | undefined
>;
const { $gettext } = useGettext();

const hasLoadingError = ref(false);
const displayDataByAlias: Ref<NodeValueDisplayDataLookup | null> = ref(null);

const descriptorAliases = computed(() => {
    const matches = props.component.config.descriptor.matchAll(/<(.*?)>/g);
    return [
        ...matches.map((match: RegExpMatchArray) => {
            return match[1];
        }),
    ];
});

const descriptor = computed(() => {
    if (!nodePresentationLookup.value || !displayDataByAlias.value) {
        return null;
    }

    let returnVal = props.component.config.descriptor;
    descriptorAliases.value.forEach((alias: string) => {
        const firstValue =
            displayDataByAlias.value![alias]?.[0]?.display_values[0];
        if (firstValue) {
            returnVal = returnVal.replace(`<${alias}>`, firstValue);
        }
    });

    return returnVal;
});

async function fetchData() {
    try {
        displayDataByAlias.value = await fetchNodeTileData(
            resourceInstanceId,
            descriptorAliases.value,
        );
        hasLoadingError.value = false;
    } catch {
        hasLoadingError.value = true;
    }
}

onMounted(fetchData);
</script>

<template>
    <Panel style="border: 0">
        <template #header>
            <h2>{{ descriptor }}</h2>
        </template>
        <Message
            v-if="hasLoadingError"
            severity="error"
            style="width: fit-content"
        >
            {{ $gettext("Unable to fetch resource") }}
        </Message>
    </Panel>
</template>

<style scoped>
:deep(.p-panel-header) {
    justify-content: center;
    margin: 0;
}

:deep(.p-panel-header) h2 {
    font-size: 2rem;
    margin: 1rem;
}
</style>
