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
    ReferenceDetails,
} from "@/arches_modular_reports/ModularReport/types";

const { value, userIsRdmAdmin = false } = defineProps<{
    value: NodeData | null;
    userIsRdmAdmin?: boolean;
}>();

const { $gettext } = useGettext();

const displayValue = computed(() => value?.display_value);
const nodeValue = computed(() => value?.node_value);
const details = computed(() => value?.details);
</script>

<template>
    <dd v-if="value === null || nodeValue === null">
        {{ $gettext("None") }}
    </dd>
    <div
        v-else-if="(details as ResourceDetails[])[0]?.resource_id"
        style="flex-direction: column"
    >
        <dd
            v-for="instanceDetail in details as ResourceDetails[]"
            :key="instanceDetail.resource_id"
        >
            <Button
                as="a"
                variant="link"
                target="_blank"
                :href="arches.urls.resource_report + instanceDetail.resource_id"
            >
                {{ instanceDetail.display_value }}
            </Button>
        </dd>
    </div>
    <div
        v-else-if="(details as ConceptDetails[])[0]?.concept_id"
        style="flex-direction: column"
    >
        <div v-if="userIsRdmAdmin">
            <dd
                v-for="conceptDetail in details as ConceptDetails[]"
                :key="conceptDetail.concept_id"
            >
                <Button
                    as="a"
                    variant="link"
                    target="_blank"
                    :href="arches.urls.rdm + conceptDetail.concept_id"
                >
                    {{ conceptDetail.value }}
                </Button>
            </dd>
        </div>
        <div v-else>
            <dd>{{ displayValue }}</dd>
        </div>
    </div>
    <dd v-else-if="(nodeValue as URLDetails)?.url">
        <Button
            as="a"
            variant="link"
            target="_blank"
            :href="(nodeValue as URLDetails).url"
        >
            {{
                (nodeValue as URLDetails).url_label ||
                (nodeValue as URLDetails).url
            }}
        </Button>
    </dd>
    <div
        v-else-if="(details as ReferenceDetails[])[0]?.list_item_id"
        style="flex-direction: column"
    >
        <dd
            v-for="resourceDetail in details as ReferenceDetails[]"
            :key="resourceDetail.list_item_id"
        >
            <Button
                as="a"
                variant="link"
                target="_blank"
                :href="(resourceDetail as ReferenceDetails).uri"
            >
                {{
                    (resourceDetail as ReferenceDetails).display_value ||
                    (resourceDetail as ReferenceDetails).uri
                }}
            </Button>
        </dd>
    </div>
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
