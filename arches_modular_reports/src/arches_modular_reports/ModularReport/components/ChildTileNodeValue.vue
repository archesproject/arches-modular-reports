<script setup lang="ts">
import arches from "arches";

import { computed } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "primevue/button";

import type {
    ConceptDetails,
    NodeData,
    ResourceDetails,
    URLDetails,
} from "@/arches_modular_reports/ModularReport/types";

const { nodeValue, userIsRdmAdmin = false } = defineProps<{
    nodeValue: NodeData | null;
    userIsRdmAdmin?: boolean;
}>();

const { $gettext } = useGettext();

const displayValue = computed(() => nodeValue?.display_value);
const interchangeValue = computed(() => nodeValue?.interchange_value);
</script>

<template>
    <dd v-if="nodeValue === null">{{ $gettext("(None)") }}</dd>
    <dd v-else-if="interchangeValue === null">{{ displayValue }}</dd>
    <div
        v-else-if="
            Array.isArray(interchangeValue) && interchangeValue[0]?.resourceId
        "
        style="flex-direction: column"
    >
        <dd
            v-for="instanceDetail in interchangeValue as ResourceDetails[]"
            :key="instanceDetail.resourceId"
        >
            <Button
                as="a"
                variant="link"
                target="_blank"
                :href="arches.urls.resource_report + instanceDetail.resourceId"
            >
                {{ instanceDetail.display_value }}
            </Button>
        </dd>
    </div>
    <div v-else-if="(interchangeValue as ConceptDetails).concept_id">
        <dd v-if="userIsRdmAdmin">
            <Button
                as="a"
                variant="link"
                target="_blank"
                :href="
                    arches.urls.rdm +
                    (interchangeValue as ConceptDetails).concept_id
                "
            >
                {{ displayValue }}
            </Button>
        </dd>
        <dd v-else>{{ displayValue }}</dd>
    </div>
    <div
        v-else-if="
            Array.isArray(interchangeValue) && interchangeValue[0]?.concept_id
        "
        style="flex-direction: column"
    >
        <div v-if="userIsRdmAdmin">
            <dd
                v-for="conceptDetail in interchangeValue as ConceptDetails[]"
                :key="conceptDetail.concept_id"
            >
                <Button
                    as="a"
                    variant="link"
                    target="_blank"
                    :href="
                        arches.urls.rdm +
                        (conceptDetail as ConceptDetails).concept_id
                    "
                >
                    {{ conceptDetail.value }}
                </Button>
            </dd>
        </div>
        <div v-else>
            <dd>{{ displayValue }}</dd>
        </div>
    </div>
    <dd v-else-if="(interchangeValue as URLDetails).url">
        <Button
            as="a"
            variant="link"
            target="_blank"
            :href="(interchangeValue as URLDetails).url"
        >
            {{
                (interchangeValue as URLDetails).url_label ||
                (interchangeValue as URLDetails).url
            }}
        </Button>
    </dd>
    <dd v-else>{{ displayValue }}</dd>
</template>

<style scoped>
dd {
    text-align: start;
}

.p-button {
    font-size: inherit;
    padding: 0;
}
</style>
