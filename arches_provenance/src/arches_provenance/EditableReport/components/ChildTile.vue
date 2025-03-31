<script setup lang="ts">
import arches from "arches";

import { inject } from "vue";

import Button from "primevue/button";

import type { Ref } from "vue";
import type {
    ConceptDetails,
    LabelBasedNode,
    LabelBasedTile,
    NodePresentationLookup,
    ResourceDetails,
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
const nodeAliasValuePairs: [string, LabelBasedNode][] = Object.entries(
    Object.values(singleTileData)[0] ?? [],
).filter(([nodeAlias]) => !nodeAlias.startsWith("@"));
const firstAlias = nodeAliasValuePairs[0][0];

const marginUnit = 1.5;
const marginUnitRem = `${marginUnit}rem`;
const cardIndentation = `${2.5 + depth * marginUnit}rem`;

const visibleChildren = children.filter(
    (child) => tileIdFromChild(child) !== null,
);

function tileIdFromChild(child: LabelBasedTile): string | null {
    const { [childKey]: _grandchildren, ...singleTileData } = child;
    if (singleTileData === null) {
        return null;
    }
    const firstNodeData = Object.values(singleTileData)[0];
    if (firstNodeData === null) {
        return null;
    }
    return (firstNodeData as LabelBasedNode)["@tile_id"];
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
            {{ nodePresentationLookup?.[firstAlias].card_name }}
        </summary>
        <dl>
            <div
                v-for="[nodeAlias, nodeValue] in nodeAliasValuePairs"
                :key="nodeAlias"
                class="node-pair"
            >
                <!-- nodeValue is null if this is a hidden node -->
                <template v-if="nodeValue">
                    <dt class="p-datatable-column-title">
                        {{ bestWidgetLabel(nodeAlias) }}
                    </dt>
                    <template v-if="nodeValue.instance_details?.length">
                        <div style="flex-direction: column">
                            <dd
                                v-for="instanceDetail in nodeValue.instance_details as ResourceDetails[]"
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
                                    {{ instanceDetail.display_value }}
                                </Button>
                            </dd>
                        </div>
                    </template>
                    <template v-else-if="nodeValue.concept_details?.length">
                        <div style="flex-direction: column">
                            <dd
                                v-for="conceptDetail in nodeValue.concept_details as ConceptDetails[]"
                                :key="conceptDetail.concept_id"
                            >
                                <Button
                                    as="a"
                                    variant="link"
                                    target="_blank"
                                    :href="
                                        arches.urls.rdm +
                                        conceptDetail.concept_id
                                    "
                                >
                                    {{ conceptDetail.value }}
                                </Button>
                            </dd>
                        </div>
                    </template>
                    <template v-else-if="nodeValue.url">
                        <dd>
                            <Button
                                as="a"
                                variant="link"
                                target="_blank"
                                :href="nodeValue.url"
                            >
                                {{ nodeValue.url_label || nodeValue.url }}
                            </Button>
                        </dd>
                    </template>
                    <dd v-else>{{ nodeValue["@display_value"] }}</dd>
                </template>
            </div>
            <ChildTile
                v-for="child in visibleChildren"
                :key="tileIdFromChild(child) as string"
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

.node-pair > dd {
    text-align: start;
}

.p-button {
    font-size: inherit;
    padding: 0;
}
</style>
