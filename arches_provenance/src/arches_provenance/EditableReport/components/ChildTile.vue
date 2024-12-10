<script setup lang="ts">
import ChildTile from "@/arches_provenance/EditableReport/components/ChildTile.vue";

import type {
    LabelBasedNode,
    LabelBasedTile,
} from "@/arches_provenance/EditableReport/types";

const { data, depth } = defineProps<{ data: LabelBasedTile; depth: number }>();

const childKey = "@children";
const { [childKey]: children, ...singleTileData } = data;
const cardName = Object.keys(singleTileData)[0];
const nodeNameValuePairs = Object.entries(singleTileData[cardName]).filter(
    (pair) => !pair[0].startsWith("@"),
);

const marginUnit = 1.5;
const marginUnitRem = `${marginUnit}rem`;
const cardIndentation = `${2.5 + depth * marginUnit}rem`;

function tileIdFromChild(child: LabelBasedTile): string {
    const { [childKey]: _grandchildren, ...singleTileData } = child;
    const nodegroup = singleTileData as unknown as LabelBasedNode;
    return Object.values(nodegroup)[0]["@tile_id"];
}
</script>

<template>
    <details open="true">
        <summary>
            <strong>{{ cardName }}</strong>
        </summary>
        <dl>
            <div
                v-for="pair in nodeNameValuePairs"
                :key="pair[0]"
                class="node-pair"
            >
                <dt>{{ pair[0] }}</dt>
                <dd>{{ pair[1]["@display_value"] }}</dd>
            </div>
            <ChildTile
                v-for="child in children"
                :key="tileIdFromChild(child)"
                :data="child"
                :depth="depth + 1"
            />
        </dl>
    </details>
</template>

<style scoped>
details {
    margin-left: v-bind(cardIndentation);
    font-size: small;
}

summary {
    margin-bottom: 1.5rem;
}

dl {
    display: flex;
    flex-direction: column;
    margin-left: v-bind(marginUnitRem);
    font-size: small;
    gap: var(--p-list-gap);
}

.node-pair {
    display: flex;
    width: 50%;
    gap: 2rem;
}

.node-pair > dt {
    width: 50%;
    text-align: end;
}

.node-pair > dd {
    width: 50%;
    text-align: start;
}
</style>
