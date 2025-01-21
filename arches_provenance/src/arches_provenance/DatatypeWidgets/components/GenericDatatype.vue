<script setup lang="ts">
import type {
    NodePresentation,
    SingleTileValue,
} from "@/arches_provenance/EditableReport/types";

const props = defineProps<{
    nodePresentation: NodePresentation;
    tileValues: SingleTileValue[];
}>();
</script>

<template>
    <div class="node-container">
        <span>
            <strong>{{ props.nodePresentation.widget_label }}</strong>
        </span>
        <span
            v-for="tileValue in tileValues"
            :key="`${tileValue}`"
            class="node-value"
        >
            {{ tileValue }}
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
    overflow: unset;
}
</style>
