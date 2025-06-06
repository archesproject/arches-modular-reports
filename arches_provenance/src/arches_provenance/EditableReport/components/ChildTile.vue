<script setup lang="ts">
import arches from "arches";

import { computed, inject } from "vue";

import Button from "primevue/button";

import type { Ref } from "vue";
import type {
    ConceptDetails,
    NodePresentationLookup,
    ResourceDetails,
    TileData,
} from "@/arches_provenance/EditableReport/types";

const {
    data,
    depth,
    divider = false,
    customLabels,
    showEmptyNodes = true,
} = defineProps<{
    data: TileData;
    depth: number;
    divider?: boolean;
    customLabels?: Record<string, string>;
    showEmptyNodes?: boolean;
}>();

const nodePresentationLookup = inject("nodePresentationLookup") as Ref<
    NodePresentationLookup | undefined
>;

const marginUnit = 1.5;
const marginUnitRem = `${marginUnit}rem`;
const cardIndentation = `${2.5 + depth * marginUnit}rem`;

const nodeAliasValuePairs = computed(() => {
    return (
        Object.entries(data.aliased_data).filter(
            ([nodeAlias, nodeValue]) =>
                (showEmptyNodes || nodeValue !== null) &&
                !isTileorTiles(nodeValue) &&
                nodePresentationLookup.value![nodeAlias]?.visible,
        ) || [[]]
    );
});

const visibleChildren = computed(() => {
    return Object.entries(data.aliased_data).reduce(
        (acc, [nodeAlias, nodeValue]) => {
            if (
                (showEmptyNodes || nodeValue !== null) &&
                isTileorTiles(nodeValue) &&
                nodePresentationLookup.value![nodeAlias]?.visible
            ) {
                if (Array.isArray(nodeValue)) {
                    acc.push(...nodeValue);
                } else {
                    acc.push(nodeValue);
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
                <dd v-if="nodeValue === null">{{ $gettext("None") }}</dd>
                <div
                    v-else-if="
                        Array.isArray(nodeValue) && nodeValue[0]?.resourceId
                    "
                    style="flex-direction: column"
                >
                    <dd
                        v-for="instanceDetail in nodeValue as ResourceDetails[]"
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
                <dd v-else-if="nodeValue.concept_id">
                    <Button
                        as="a"
                        variant="link"
                        target="_blank"
                        :href="arches.urls.rdm + nodeValue.concept_id"
                    >
                        {{ nodeValue["@display_value"] }}
                    </Button>
                </dd>
                <div
                    v-else-if="nodeValue.concept_details?.length"
                    style="flex-direction: column"
                >
                    <dd
                        v-for="conceptDetail in nodeValue.concept_details as ConceptDetails[]"
                        :key="conceptDetail.concept_id"
                    >
                        <Button
                            as="a"
                            variant="link"
                            target="_blank"
                            :href="arches.urls.rdm + conceptDetail.concept_id"
                        >
                            {{ conceptDetail.value }}
                        </Button>
                    </dd>
                </div>
                <dd v-else-if="nodeValue.url">
                    <Button
                        as="a"
                        variant="link"
                        target="_blank"
                        :href="nodeValue.url"
                    >
                        {{ nodeValue.url_label || nodeValue.url }}
                    </Button>
                </dd>
                <dd v-else>{{ nodeValue }}</dd>
            </div>
            <ChildTile
                v-for="child in visibleChildren"
                :key="child.tileid!"
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
