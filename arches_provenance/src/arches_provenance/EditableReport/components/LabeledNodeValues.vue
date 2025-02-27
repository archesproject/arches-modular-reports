<script setup lang="ts">
import { computed } from "vue";

import Button from "primevue/button";

import { RESOURCE_LIMIT_FOR_HEADER } from "@/arches_provenance/constants.ts";

import type { NodeValueDisplayData } from "@/arches_provenance/EditableReport/types";

const props = defineProps<{
    widgetLabel: string;
    displayData: NodeValueDisplayData[];
}>();

const truncatedDisplayData = computed(() => {
    // The tiles were already fetched with a limit, but we unpack
    // multiple display values for *-list datatypes, so truncate.
    var counter = 0;
    return props.displayData.reduce((acc, tileData) => {
        counter += tileData.display_values.length;
        const excess = counter - RESOURCE_LIMIT_FOR_HEADER;
        if (excess > 0) {
            acc.push({
                display_values: tileData.display_values.slice(0, -excess),
                links: tileData.links.slice(0, -excess),
            });
        } else {
            acc.push(tileData);
        }
        return acc;
    }, [] as NodeValueDisplayData[]);
});
</script>

<template>
    <div class="node-container">
        <dt>
            <strong>{{ widgetLabel }}</strong>
        </dt>
        <div class="node-values-container">
            <template
                v-for="nodeValueDisplayData in truncatedDisplayData"
                :key="nodeValueDisplayData.display_values"
            >
                <template v-if="nodeValueDisplayData.links.length">
                    <dd
                        v-for="link in nodeValueDisplayData.links"
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
                <template v-else>
                    <dd
                        v-for="innerValue in nodeValueDisplayData.display_values"
                        :key="innerValue"
                        class="node-value"
                    >
                        {{ innerValue }}
                    </dd>
                </template>
            </template>
        </div>
    </div>
</template>

<style scoped>
.node-container {
    display: flex;
    gap: 1rem;
    max-height: 18rem;
}

.node-values-container {
    height: 100%;
    overflow: auto;
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
