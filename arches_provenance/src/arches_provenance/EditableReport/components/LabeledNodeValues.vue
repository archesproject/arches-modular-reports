<script setup lang="ts">
import Button from "primevue/button";

import type { NodeValueDisplayData } from "@/arches_provenance/EditableReport/types";

const props = defineProps<{
    widgetLabel: string;
    displayData: NodeValueDisplayData[];
}>();
</script>

<template>
    <div class="node-container">
        <dt>
            <strong>{{ widgetLabel }}</strong>
        </dt>
        <div class="node-values-container">
            <template
                v-for="nodeValueDisplayData in props.displayData"
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
}

.p-button {
    font-size: inherit;
    padding: 0;
    align-items: start;
    overflow: unset;
}
</style>
