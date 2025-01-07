<script setup lang="ts">
import arches from "arches";

import { inject } from "vue";

import Button from "primevue/button";

import type {
    LabelBasedNode,
    LabelBasedTile,
    NodePresentationLookup,
} from "@/arches_provenance/EditableReport/types";

const {
    data,
    depth,
    divider = false,
} = defineProps<{ data: LabelBasedTile; depth: number; divider?: boolean }>();

const nodePresentationLookup = inject(
    "nodePresentationLookup",
) as NodePresentationLookup;

const childKey = "@children";
const { [childKey]: children, ...singleTileData } = data;
const cardName = Object.keys(singleTileData)[0];
const nodeNameValuePairs = Object.entries(singleTileData[cardName]).filter(
    ([nodeName]) => !nodeName.startsWith("@"),
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
    <div
        v-if="divider"
        class="divider"
        role="presentation"
    ></div>
    <details open="true">
        <summary>
            <strong>{{ nodePresentationLookup[cardName].card_name }}</strong>
        </summary>
        <dl>
            <div
                v-for="[nodeName, nodeValue] in nodeNameValuePairs"
                :key="nodeName"
                class="node-pair"
            >
                <dt>{{ nodePresentationLookup[nodeName].widget_label }}</dt>
                <template v-if="nodeValue.instance_details?.length">
                    <dd
                        v-for="instanceDetail in nodeValue.instance_details"
                        :key="instanceDetail.resourceId"
                    >
                        <Button
                            as="a"
                            variant="link"
                            :href="
                                arches.urls.resource_report +
                                instanceDetail.resourceId
                            "
                        >
                            {{ nodeValue["@display_value"] }}
                        </Button>
                    </dd>
                </template>
                <dd v-else>{{ nodeValue["@display_value"] }}</dd>
            </div>
            <ChildTile
                v-for="child in children"
                :key="tileIdFromChild(child)"
                :divider="true"
                :data="child"
                :depth="depth + 1"
            />
        </dl>
    </details>
</template>

<style scoped>
.divider {
    height: 2px;
    margin: 2rem;
    background: var(--p-content-border-color);
}

details {
    margin-top: var(--p-list-gap);
    margin-left: v-bind(cardIndentation);
    font-size: small;
}

summary {
    margin-bottom: 1.5rem;
    /* https://github.com/twbs/bootstrap/issues/21060 */
    display: list-item;
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

.p-button {
    font-size: inherit;
    padding: 0;
}
</style>
