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
    Object.values(singleTileData)[0],
).filter(([nodeAlias]) => !nodeAlias.startsWith("@"));
const firstAlias = nodeAliasValuePairs[0][0];

const marginUnit = 1.5;
const cardIndentation = `${2.5 + depth * marginUnit}rem`;

function tileIdFromChild(child: LabelBasedTile): string {
    const { [childKey]: _grandchildren, ...singleTileData } = child;
    const nodegroup = singleTileData as unknown as LabelBasedNode;
    // This will not be null since a hidden node won't have children.
    return (Object.values(nodegroup)[0] as unknown as LabelBasedNode)[
        "@tile_id"
    ];
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
        <table style="width: 100%">
            <tr
                v-for="[nodeAlias, nodeValue] in nodeAliasValuePairs"
                :key="nodeAlias"
                class="node-pair"
            >
                <!-- nodeValue is null if this is a hidden node -->
                <template v-if="nodeValue">
                    <td style="text-align: right; width: 25%">
                        {{ bestWidgetLabel(nodeAlias) }}
                    </td>
                    <template v-if="nodeValue.instance_details?.length">
                        <td style="flex-direction: column">
                            <div
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
                            </div>
                        </td>
                    </template>
                    <template v-else-if="nodeValue.concept_details?.length">
                        <td style="flex-direction: column">
                            <div
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
                            </div>
                        </td>
                    </template>
                    <template v-else-if="nodeValue.url">
                        <td>
                            <Button
                                as="a"
                                variant="link"
                                target="_blank"
                                :href="nodeValue.url"
                            >
                                {{ nodeValue.url_label }}
                            </Button>
                        </td>
                    </template>
                    <td v-else>{{ nodeValue["@display_value"] }}</td>
                </template>
            </tr>
            <tr>
                <td colspan="2">
                    <ChildTile
                        v-for="child in children"
                        :key="tileIdFromChild(child)"
                        :divider="true"
                        :data="child"
                        :depth="depth + 1"
                        :custom-labels
                    />
                </td>
            </tr>
        </table>
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
}

td {
    padding: 0px;
}

.node-pair {
    display: flex;
    gap: 2rem;
}

.node-pair > td:first-child {
    font-weight: bold;
}

.p-button {
    font-size: inherit;
    padding: 0;
}
</style>
