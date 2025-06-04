<script setup lang="ts">
import { computed, inject, ref } from "vue";
import { useGettext } from "vue3-gettext";

import Panel from "primevue/panel";
import Tree from "primevue/tree";

import { uniqueId } from "@/arches_provenance/EditableReport/utils.ts";

import type { Ref } from "vue";
import type { TreeExpandedKeys, TreeSelectionKeys } from "primevue/tree";
import type { TreeNode } from "primevue/treenode";
import type {
    NodePresentationLookup,
    ResourceDetails,
} from "@/arches_provenance/EditableReport/types";
import type {
    ResourceData,
    NodeValue,
    TileData,
} from "@/arches_provenance/EditableReport/components/ResourceEditor/types.ts";

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
/// todo(jtw): look into un-reffing this.
const nodePresentationLookup = inject<Ref<NodePresentationLookup>>(
    "nodePresentationLookup",
)!;

const tree = computed(() => {
    // todo(jtw): consider moving helpers out of this file
    const topCards = Object.entries(props.resourceData.aliased_data).reduce<
        TreeNode[]
    >((acc, [alias, data]) => {
        acc.push(processNodegroup(alias, data, "root"));
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
                acc.push(processNodegroup(alias, data, tile.tileid));
            } else {
                acc.push(processNode(alias, data, tile.tileid, nodegroupAlias));
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
    data: NodeValue,
    tileId: string | null,
    nodegroupAlias: string,
): TreeNode {
    const localizedLabel = $gettext("%{label}: %{labelData}", {
        label: nodePresentationLookup.value[alias].widget_label,
        labelData: getDisplayValue(
            data,
            nodePresentationLookup.value[alias].datatype,
            tileId,
        ),
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
                key: tile.tileid ?? uniqueId(0),
                label: idx.toString(),
                data: { ...tile, alias: nodegroupAlias },
                children: processTileData(tile, nodegroupAlias),
            };
            result.label = result.children[0].label as string;
            return result;
        }),
    };
}

/*
TODO: we can remove this function by having the serializer calc
all node display values. That's 🤌, but it's follow-up work.
*/
function getDisplayValue(
    value: NodeValue,
    datatype: string,
    tileId: string | null,
): string {
    if (!tileId) {
        return $gettext("(empty)");
    }
    // TODO: more specific types for `value` arg
    if (value === null || value === undefined) {
        return $gettext("None");
    }
    switch (datatype) {
        case "semantic":
            return "";
        case "concept":
        case "concept-list":
            return value["@display_value"]!;
        case "resource-instance":
            return (value as unknown as ResourceDetails).display_value;
        case "resource-instance-list":
            return (value as unknown as ResourceDetails[])
                .map((resourceDetails) => resourceDetails.display_value)
                .join(", ");
        case "number":
            return value.toLocaleString();
        case "url": {
            const urlPair = value as { url: string; url_label: string };
            return urlPair.url_label || urlPair.url;
        }
        case "non-localized-string":
        case "string": // currently resolves to single string
        default:
            // TODO: handle other datatypes, batten down types.
            return value as unknown as string;
    }
}

function isTileOrTiles(nodeValue: NodeValue | TileData[]) {
    const tiles = Array.isArray(nodeValue) ? nodeValue : [nodeValue];
    return tiles.every((tile) => tile?.aliased_data);
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
        <p>Tree</p>
        <Tree
            v-model:selection-keys="selectedKeys"
            v-model:expanded-keys="expandedKeys"
            :value="tree"
            selection-mode="single"
            @node-select="onNodeSelect"
        />
    </Panel>
</template>
