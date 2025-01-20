<script setup lang="ts">
import arches from "arches";

import Button from "primevue/button";

import type {
    NodePresentation,
    TileValue,
} from "@/arches_provenance/EditableReport/types";

const props = defineProps<{
    nodePresentation: NodePresentation;
    tileValue: TileValue;
}>();
</script>

<template>
    <div class="node-container">
        <span>
            <strong>{{ props.nodePresentation.widget_label }}</strong>
        </span>
        <template v-if="tileValue.instance_details?.length">
            <Button
                v-for="relatedResourceDetail in tileValue.instance_details"
                :key="relatedResourceDetail.resourceId"
                as="a"
                target="_blank"
                variant="link"
                :href="
                    arches.urls.resource_report +
                    relatedResourceDetail.resourceId
                "
            >
                {{ tileValue["@display_value"] }}
            </Button>
        </template>
        <span
            v-else
            class="node-value"
        >
            {{ tileValue["@display_value"] }}
        </span>
    </div>
</template>

<style scoped>
.node-container {
    display: flex;
    gap: 10px;
}

.node-value {
    overflow-wrap: anywhere;
}

.p-button {
    font-size: inherit;
    padding: 0;
    align-items: start;
}
</style>
