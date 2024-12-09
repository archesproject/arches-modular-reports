<script setup lang="ts">
import ChildTile from "@/arches_provenance/EditableReport/components/ChildTile.vue";

import type { LabelBasedTile } from "@/arches_provenance/EditableReport/types";

const { data, depth } = defineProps<{ data: LabelBasedTile; depth: number }>();

const childKey = "@children";
const { [childKey]: children, ...singleTileData } = data;
const cardName = Object.keys(singleTileData)[0];
const nodeNameValuePairs = Object.entries(singleTileData[cardName]).filter(
    (pair) => !pair[0].startsWith("@"),
);

const indentation = 2.5 + depth * 1.5 + "rem";
</script>

<template>
    <div class="node-data">
        <h5>{{ cardName }}</h5>
        <span
            v-for="pair in nodeNameValuePairs"
            :key="pair[0]"
            style="margin-left: 1.5rem; font-size: small"
        >
            {{ pair[0] }}: {{ pair[1]["@display_value"] }}
        </span>
        <!-- TODO: test and add key -->
        <ChildTile
            v-for="child in children"
            :data="child"
            :depth="depth + 1"
        />
    </div>
</template>

<style scoped>
.node-data {
    margin-left: v-bind(indentation);
}
</style>
