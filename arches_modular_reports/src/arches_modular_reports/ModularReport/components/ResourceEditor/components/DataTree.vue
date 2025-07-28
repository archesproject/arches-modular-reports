<script setup lang="ts">
import { computed, inject, ref } from "vue";
import { useGettext } from "vue3-gettext";

import Panel from "primevue/panel";
import Tree from "primevue/tree";

import { uniqueId } from "@/arches_modular_reports/ModularReport/utils.ts";

import type { Ref } from "vue";
import type { TreeExpandedKeys, TreeSelectionKeys } from "primevue/tree";
import type { TreeNode } from "primevue/treenode";
import type { NodePresentationLookup } from "@/arches_modular_reports/ModularReport/types";
import type {
    ResourceData,
    NodeData,
    NodegroupData,
    TileData,
    URLDetails,
} from "@/arches_modular_reports/ModularReport/types.ts";

const { $gettext } = useGettext();

const props = defineProps<{ resourceData: ResourceData }>();

const selectedKeys: Ref<TreeSelectionKeys> = ref({});
const expandedKeys: Ref<TreeExpandedKeys> = ref({});
const { setSelectedNodegroupAlias } = inject<{
    setSelectedNodegroupAlias: (nodegroupAlias: string | null) => void;
}>("selectedNodegroupAlias")!;
const { setSelectedTileId } = inject<{
    setSelectedTileId: (tileId: string | null | undefined) => void;
}>("selectedTileId")!;
const nodePresentationLookup = inject<Ref<NodePresentationLookup>>(
    "nodePresentationLookup",
)!;

const tree = computed(() => {
    const topCards = Object.entries(props.resourceData.aliased_data).reduce<
        TreeNode[]
    >((acc, [alias, data]) => {
        acc.push(processNodegroup(alias, data as TileData | TileData[], null));
        return acc;
    }, []);
    return topCards.sort((a, b) => {
        return (
            nodePresentationLookup.value[a.data.alias].card_order -
            nodePresentationLookup.value[b.data.alias].card_order
        );
    });
});

function processTileData(tile: TileData, nodegroupAlias: string): TreeNode[] {
    const tileValues = Object.entries(tile.aliased_data).reduce<TreeNode[]>(
        (acc, [alias, data]) => {
            if (isTileOrTiles(data)) {
                acc.push(
                    processNodegroup(
                        alias,
                        data as TileData | TileData[],
                        tile.tileid,
                    ),
                );
            } else if (nodePresentationLookup.value[alias].visible) {
                acc.push(
                    processNode(
                        alias,
                        data as NodeData | null,
                        tile.tileid,
                        nodegroupAlias,
                    ),
                );
            }
            return acc;
        },
        [],
    );
    return tileValues.sort((a, b) => {
        return (
            nodePresentationLookup.value[a.data.alias].widget_order -
            nodePresentationLookup.value[b.data.alias].widget_order
        );
    });
}

function processNode(
    alias: string,
    data: NodeData | null,
    tileId: string | null,
    nodegroupAlias: string,
): TreeNode {
    const localizedLabel = $gettext("%{label}: %{labelData}", {
        label: nodePresentationLookup.value[alias].widget_label,
        labelData: extractAndOverrideDisplayValue(data),
    });
    return {
        key: `${alias}-node-value-for-${tileId}`,
        label: localizedLabel,
        data: { alias: alias, tileid: tileId, nodegroupAlias },
    };
}

function processNodegroup(
    nodegroupAlias: string,
    tileOrTiles: TileData | TileData[],
    parentTileId: string | null,
): TreeNode {
    if (Array.isArray(tileOrTiles)) {
        return createCardinalityNWrapper(
            nodegroupAlias,
            tileOrTiles,
            parentTileId,
        );
    } else {
        return {
            key: `${nodegroupAlias}-child-of-${parentTileId ?? uniqueId(0)}`,
            label: nodePresentationLookup.value[nodegroupAlias].card_name,
            data: { ...tileOrTiles, alias: nodegroupAlias },
            children: processTileData(tileOrTiles, nodegroupAlias),
        };
    }
}

function createCardinalityNWrapper(
    nodegroupAlias: string,
    tiles: TileData[],
    parentTileId: string | null,
): TreeNode {
    return {
        key: `${nodegroupAlias}-child-of-${parentTileId ?? uniqueId(0)}`,
        label: nodePresentationLookup.value[nodegroupAlias].card_name,
        data: { tileid: parentTileId, alias: nodegroupAlias },
        children: tiles.map((tile, idx) => {
            const result = {
                key: tile.tileid ?? uniqueId(0).toString(),
                label: idx.toString(),
                data: { ...tile, alias: nodegroupAlias },
                children: processTileData(tile, nodegroupAlias),
            };
            result.label = result.children[0].label as string;
            return result;
        }),
    };
}

function extractAndOverrideDisplayValue(value: NodeData | null): string {
    if (value === null) {
        return $gettext("(Empty)");
    }
    if (value.display_value.includes("url_label")) {
        // The URL datatype deserves a better display value in core Arches.
        const urlPair = value.node_value as URLDetails;
        return urlPair.url_label || urlPair.url;
    }
    return value.display_value;
}

function isTileOrTiles(nodeData: NodeData | NodegroupData | null) {
    const tiles = Array.isArray(nodeData) ? nodeData : [nodeData];
    return tiles.every((tile) => (tile as TileData)?.aliased_data);
}

function onNodeSelect(node: TreeNode) {
    setSelectedNodegroupAlias(node.data.nodegroupAlias ?? node.data.alias);
    setSelectedTileId(node.data.tileid);
}
</script>

<template>
    <Panel
        :header="$gettext('Data Tree')"
        :pt="{ header: { style: { padding: '1rem' } } }"
    >
        <Tree
            v-model:selection-keys="selectedKeys"
            v-model:expanded-keys="expandedKeys"
            :value="tree"
            selection-mode="single"
            @node-select="onNodeSelect"
        />
    </Panel>
</template>
