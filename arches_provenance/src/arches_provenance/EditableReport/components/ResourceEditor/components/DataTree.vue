<script setup lang="ts">
import { computed, inject, ref } from "vue";
import { useGettext } from "vue3-gettext";

import Panel from "primevue/panel";
import Tree from "primevue/tree";

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
const { setSelectedNodeAlias } = inject<{
    setSelectedNodeAlias: (nodeAlias: string | null) => void;
}>("selectedNodeAlias")!;
const { setSelectedTileId } = inject<{
    setSelectedTileId: (tileId: string | null) => void;
}>("selectedTileId")!;
/// todo(jtw): look into un-reffing this.
const nodePresentationLookup = inject<Ref<NodePresentationLookup>>(
    "nodePresentationLookup",
)!;

const tree = computed(() => {
    // todo(jtw): consider moving helpers out of this file
    return Object.entries(props.resourceData.aliased_data).reduce<TreeNode[]>(
        (acc, [alias, data]) => {
            acc.push(processNodegroup(alias, data, "root"));
            return acc;
        },
        [],
    );
});

function processTileData(tile: TileData): TreeNode[] {
    return Object.entries(tile.aliased_data).reduce<TreeNode[]>(
        (acc, [alias, data]) => {
            if (isTileOrTiles(data)) {
                acc.push(processNodegroup(alias, data, tile.tileid));
            } else {
                acc.push(processNode(alias, data, tile.tileid));
            }
            return acc;
        },
        [],
    );
}

function processNode(alias: string, data: NodeValue, tileId: string): TreeNode {
    const localizedLabel = $gettext("%{label}: %{labelData}", {
        label: nodePresentationLookup.value[alias].widget_label,
        labelData:
            getDisplayValue(
                data,
                nodePresentationLookup.value[alias].datatype,
            ) ?? $gettext("None"),
    });
    return {
        key: `${alias}-node-value-for-${tileId}`,
        label: localizedLabel,
        data: { alias: alias, tileid: tileId },
    };
}

function processNodegroup(
    nodegroupAlias: string,
    tileOrTiles: TileData | TileData[],
    parentTileId: string,
): TreeNode {
    if (Array.isArray(tileOrTiles)) {
        return createCardinalityNWrapper(
            nodegroupAlias,
            tileOrTiles,
            parentTileId,
        );
    } else {
        return {
            key: `${nodegroupAlias}-child-of-${parentTileId}`,
            label: nodePresentationLookup.value[nodegroupAlias].card_name,
            data: { ...tileOrTiles, alias: nodegroupAlias },
            children: processTileData(tileOrTiles),
        };
    }
}

function createCardinalityNWrapper(
    nodegroupAlias: string,
    tiles: TileData[],
    parentTileId: string,
): TreeNode {
    return {
        key: `${nodegroupAlias}-child-of-${parentTileId}`,
        label: nodePresentationLookup.value[nodegroupAlias].card_name,
        data: { tileid: parentTileId, alias: nodegroupAlias },
        children: tiles.map((tile, idx) => {
            const result = {
                key: tile.tileid,
                label: idx.toString(),
                data: { ...tile, alias: nodegroupAlias },
                children: processTileData(tile),
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
function getDisplayValue(value: NodeValue, datatype: string): string | null {
    // TODO: more specific types for `value` arg
    if (value === null || value === undefined) {
        return "";
    }
    switch (datatype) {
        case null:
        case "semantic":
            return null;
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
    setSelectedNodeAlias(node.data.alias);
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
