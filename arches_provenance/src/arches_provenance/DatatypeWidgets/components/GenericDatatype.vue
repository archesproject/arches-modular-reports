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
        <dt>
            <strong>{{ props.nodePresentation.widget_label }}</strong>
        </dt>
        <div class="node-values-container">
            <template
                v-for="tile in props.displayData"
                :key="tile.display_values"
            >
                <template v-if="tile.links.length === 0">
                    <dd
                        v-for="innerValue in tile.display_values"
                        :key="innerValue"
                        class="node-value"
                    >
                        {{ innerValue }}
                    </dd>
                </template>
                <template v-else>
                    <dd
                        v-for="link in tile.links"
                        :key="JSON.stringify(link)"
                        class="node-value"
                    >
                        <Button
                            as="a"
                            class="node-value"
                            target="_blank"
                            variant="link"
                            :href="link.link"
                        >
                            {{ link.label }}
                        </Button>
                    </dd>
                </template>
            </template>
        </div>
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
