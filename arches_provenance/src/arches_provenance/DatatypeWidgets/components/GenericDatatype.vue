<script setup lang="ts">
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
        <span class="node-value">{{ tileValue }}</span>
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
</style>
