<script setup lang="ts">
import Button from "primevue/button";

import type {
    NodePresentation,
    TileDisplayData,
} from "@/arches_provenance/EditableReport/types";

const props = defineProps<{
    nodePresentation: NodePresentation;
    displayData: TileDisplayData[];
}>();
</script>

<template>
    <div class="node-container">
        <span>
            <strong>{{ props.nodePresentation.widget_label }}</strong>
        </span>
        <template
            v-for="displayData in props.displayData"
            :key="displayData.display_value"
        >
            <template v-if="displayData.links.length === 0">
                <span class="node-value">
                    {{ displayData.display_value }}
                </span>
            </template>
            <Button
                v-for="link in displayData.links"
                :key="JSON.stringify(link)"
                as="a"
                class="node-value"
                target="_blank"
                variant="link"
                :href="link.link"
            >
                {{ displayData.display_value }}
            </Button>
        </template>
    </div>
</template>

<style scoped>
.node-container {
    display: flex;
    gap: 10px;
}

.node-value {
    align-items: unset;
    overflow-wrap: anywhere;
}

.p-button {
    font-size: inherit;
    padding: 0;
    align-items: start;
    overflow: unset;
}
</style>
