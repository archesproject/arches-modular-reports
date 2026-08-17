<script setup lang="ts">
import { computed, inject } from "vue";

import ChildTileNodeValue from "@/arches_modular_reports/ModularReport/components/ChildTileNodeValue.vue";

import type { Ref } from "vue";
import type {
    NodeData,
    NodegroupData,
    NodePresentationLookup,
    TileData,
} from "@/arches_modular_reports/ModularReport/types";

const {
    data,
    depth,
    divider = false,
    customLabels,
    showEmptyNodes = true,
    userIsRdmAdmin = false,
} = defineProps<{
    data: TileData;
    depth: number;
    divider?: boolean;
    customLabels?: Record<string, string>;
    showEmptyNodes?: boolean;
    userIsRdmAdmin?: boolean;
}>();

const nodePresentationLookup = inject("nodePresentationLookup") as Ref<
    NodePresentationLookup | undefined
>;

const marginUnit = 1.5;
const marginUnitRem = `${marginUnit}rem`;
const cardIndentation = `${2.5 + depth * marginUnit}rem`;

const nodeAliasValuePairs = computed(() => {
    const filtered = Object.entries(data.aliased_data).filter(shouldShowNode);
    return (filtered || [[]]) as [string, NodeData][];
});

const visibleChildren = computed(() => {
    return Object.entries(data.aliased_data).reduce(
        (acc, [nodeAlias, nodeValue]) => {
            if (
                (showEmptyNodes || nodeValueIsEmpty(nodeValue)) &&
                isTileorTiles(nodeValue) &&
                nodePresentationLookup.value![nodeAlias]?.visible
            ) {
                if (Array.isArray(nodeValue)) {
                    acc.push(...nodeValue);
                } else {
                    acc.push(nodeValue as TileData);
                }
            }
            return acc;
        },
        [] as TileData[],
    );
});

function isTileorTiles(input: unknown) {
    return (
        (input as TileData)?.tileid ||
        (Array.isArray(input) && input.every((item) => item.tileid))
    );
}

function nodeValueIsEmpty(nodeValue: NodeData | NodegroupData | null) {
    return nodeValue === null || (nodeValue as NodeData).node_value === null;
}

function shouldShowNode(
    nodeAliasValuePair: [string, NodeData | NodegroupData | null],
) {
    const [nodeAlias, nodeValue] = nodeAliasValuePair;
    return (
        (showEmptyNodes || nodeValueIsEmpty(nodeValue)) &&
        !isTileorTiles(nodeValue) &&
        nodePresentationLookup.value![nodeAlias]?.visible
    );
}

function bestWidgetLabel(nodeAlias: string) {
    return (
        customLabels?.[nodeAlias] ??
        nodePresentationLookup.value?.[nodeAlias].widget_label ??
        nodeAlias
    );
}
</script>

<template>
    <div
        v-if="divider"
        class="divider"
        role="presentation"
    ></div>
    <details open="true">
        <summary class="p-datatable-column-title">
            {{
                nodePresentationLookup?.[nodeAliasValuePairs[0]?.[0]]?.card_name
            }}
        </summary>
        <dl>
            <div
                v-for="[nodeAlias, nodeValue] in nodeAliasValuePairs"
                :key="nodeAlias"
                class="node-pair"
            >
                <dt class="p-datatable-column-title">
                    {{ bestWidgetLabel(nodeAlias) }}
                </dt>
                <ChildTileNodeValue
                    :value="nodeValue"
                    :user-is-rdm-admin="userIsRdmAdmin"
                />
            </div>
            <ChildTile
                v-for="child in visibleChildren"
                :key="child.tileid!"
                :divider="true"
                :data="child"
                :depth="depth + 1"
                :custom-labels
                :show-empty-nodes="showEmptyNodes"
                :user-is-rdm-admin="userIsRdmAdmin"
            />
        </dl>
    </details>
</template>

<style scoped>
.divider {
    height: 2px;
    margin: 1rem;
    background: var(--p-content-border-color);
}

details {
    margin-top: var(--p-list-gap);
    margin-left: v-bind(cardIndentation);
    font-size: small;
}

summary {
    /* https://github.com/twbs/bootstrap/issues/21060 */
    display: list-item;
    margin-bottom: 10px;
    font-size: 1.4rem;
}

dl {
    display: flex;
    flex-direction: column;
    margin-left: v-bind(marginUnitRem);
    margin-bottom: 1rem;
    font-size: small;
    gap: var(--p-list-gap);
}

.node-pair {
    display: flex;
    width: 60%;
}

.node-pair > dt {
    width: 40%;
    text-align: end;
    padding-inline-end: 2rem;
}
</style>
