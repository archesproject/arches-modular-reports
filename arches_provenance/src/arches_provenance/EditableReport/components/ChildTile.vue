<script setup lang="ts">
import arches from "arches";

import { inject } from "vue";

import Button from "primevue/button";

import type { Ref } from "vue";
import type {
    LabelBasedNode,
    LabelBasedTile,
    NodePresentationLookup,
} from "@/arches_provenance/EditableReport/types";

const {
    data,
    depth,
    divider = false,
    customLabels,
} = defineProps<{
    data: LabelBasedTile;
    depth: number;
    divider?: boolean;
    customLabels?: Record<string, string>;
}>();

const nodePresentationLookup = inject("nodePresentationLookup") as Ref<
    NodePresentationLookup | undefined
>;

const childKey = "@children";
const { [childKey]: children, ...singleTileData } = data;
const nodeAliasValuePairs = Object.entries(
    Object.values(singleTileData)[0],
).filter(([nodeAlias]) => !nodeAlias.startsWith("@"));
const firstAlias = nodeAliasValuePairs[0][0];

const marginUnit = 1.5;
const marginUnitRem = `${marginUnit}rem`;
const cardIndentation = `${2.5 + depth * marginUnit}rem`;

function tileIdFromChild(child: LabelBasedTile): string {
    const { [childKey]: _grandchildren, ...singleTileData } = child;
    const nodegroup = singleTileData as unknown as LabelBasedNode;
    return Object.values(nodegroup)[0]["@tile_id"];
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
        <summary>
            <strong>
                {{ nodePresentationLookup?.[firstAlias].card_name }}
            </strong>
        </summary>
        <dl>
            <div
                v-for="[nodeAlias, nodeValue] in nodeAliasValuePairs"
                :key="nodeAlias"
                class="node-pair"
            >
                <!-- TODO: update link generation pattern when refactoring backend. -->
                <dt>{{ bestWidgetLabel(nodeAlias) }}</dt>
                <template v-if="nodeValue.instance_details?.length">
                    <dd
                        v-for="instanceDetail in nodeValue.instance_details"
                        :key="instanceDetail.resourceId"
                    >
                        <Button
                            as="a"
                            variant="link"
                            target="_blank"
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
                :custom-labels
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
    margin-bottom: 1.5rem;
    /* https://github.com/twbs/bootstrap/issues/21060 */
    display: list-item;
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
