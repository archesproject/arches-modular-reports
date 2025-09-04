<script setup lang="ts">
import { computed, inject, ref, useTemplateRef, watch } from "vue";
import { useGettext } from "vue3-gettext";

import Panel from "primevue/panel";
import Tree from "primevue/tree";

import { findNodeInTree } from "@/arches_modular_reports/ModularReport/components/ResourceEditor/components/DataTree/utils/find-node-in-tree.ts";
import { generateTilePath } from "@/arches_modular_reports/ModularReport/components/ResourceEditor/components/DataTree/utils/generate-tile-path.ts";
import { generateStableKey } from "@/arches_modular_reports/ModularReport/components/ResourceEditor/components/DataTree/utils/generate-stable-key.ts";

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
import type { WidgetDirtyStates } from "@/arches_modular_reports/ModularReport/components/ResourceEditor/types.ts";

const { $gettext } = useGettext();

const { setSelectedNodegroupAlias } = inject<{
    setSelectedNodegroupAlias: (nodegroupAlias: string | null) => void;
}>("selectedNodegroupAlias")!;

const { selectedNodeAlias, setSelectedNodeAlias } = inject<{
    selectedNodeAlias: Ref<string | null>;
    setSelectedNodeAlias: (nodeAlias: string | null) => void;
}>("selectedNodeAlias")!;

const { setSelectedTileId } = inject<{
    setSelectedTileId: (tileId: string | null | undefined) => void;
}>("selectedTileId")!;

const { selectedTilePath, setSelectedTilePath } = inject<{
    selectedTilePath: Ref<Array<string | number> | null>;
    setSelectedTilePath: (path: Array<string | number> | null) => void;
}>("selectedTilePath")!;

const nodePresentationLookup = inject<Ref<NodePresentationLookup>>(
    "nodePresentationLookup",
)!;

const { resourceData, widgetDirtyStates } = defineProps<{
    resourceData: ResourceData;
    widgetDirtyStates: WidgetDirtyStates;
}>();

const treeContainerElement = useTemplateRef("treeContainerElement");

const selectedKeys: Ref<TreeSelectionKeys> = ref({});
const expandedKeys: Ref<TreeExpandedKeys> = ref({});

const tree = computed(() => {
    const rootNodes = Object.entries(resourceData.aliased_data).map(function ([
        nodegroupAlias,
        tileOrTiles,
    ]) {
        return processNodegroup(
            nodegroupAlias,
            tileOrTiles as TileData | TileData[],
            null,
            widgetDirtyStates.aliased_data as WidgetDirtyStates,
        );
    });

    return rootNodes.sort((firstNode, secondNode) => {
        return (
            nodePresentationLookup.value[firstNode.data.alias].card_order -
            nodePresentationLookup.value[secondNode.data.alias].card_order
        );
    });
});

watch(
    selectedKeys,
    (newValue, oldValue) => {
        if (newValue !== oldValue) {
            requestAnimationFrame(() => {
                const selectedTreeNode =
                    treeContainerElement.value!.querySelector(
                        ".p-tree-node-content.p-tree-node-selected",
                    );

                if (selectedTreeNode) {
                    selectedTreeNode.scrollIntoView({
                        block: "center",
                        inline: "center",
                        behavior: "smooth",
                    });
                }
            });
        }
    },
    { deep: true },
);

watch(
    [selectedNodeAlias, selectedTilePath],
    () => {
        if (!selectedTilePath.value) return;

        const { foundNode, nodePath } = findNodeInTree(
            tree.value,
            selectedTilePath.value,
        );
        if (!foundNode) return;

        expandedKeys.value = [...nodePath, foundNode].reduce(
            function (acc, node) {
                acc[node.key] = true;
                return acc;
            },
            { ...expandedKeys.value },
        );

        const currentSelectedKey = Object.keys(selectedKeys.value)[0];

        const foundNodeAlias = foundNode.children?.find(
            (child) => child.data?.alias === selectedNodeAlias.value,
        );

        let selectedNodeKey;
        if (foundNodeAlias?.key != null) {
            selectedNodeKey = foundNodeAlias.key;
        } else if (!currentSelectedKey && foundNode.key != null) {
            selectedNodeKey = foundNode.key;
        } else {
            selectedNodeKey = currentSelectedKey;
        }

        if (selectedNodeKey && currentSelectedKey !== selectedNodeKey) {
            selectedKeys.value = { [selectedNodeKey]: true };
        }
    },
    { immediate: true },
);

function processNodegroup(
    nodegroupAlias: string,
    tileOrTiles: TileData | TileData[],
    parentTileId: string | null,
    widgetDirtyStates: WidgetDirtyStates,
): TreeNode {
    if (Array.isArray(tileOrTiles)) {
        return createCardinalityNWrapper(
            nodegroupAlias,
            tileOrTiles,
            parentTileId,
            widgetDirtyStates,
        );
    }

    const tileDirtyStates = (
        widgetDirtyStates?.[nodegroupAlias] as WidgetDirtyStates
    )?.aliased_data;

    const children = processTileData(
        tileOrTiles,
        nodegroupAlias,
        tileDirtyStates as WidgetDirtyStates,
    );

    const isDirty = children.some(
        (childNode) => childNode.styleClass === "is-dirty",
    );

    return {
        key: generateStableKey(tileOrTiles),
        label: nodePresentationLookup.value[nodegroupAlias].card_name,
        data: { tileid: tileOrTiles.tileid, alias: nodegroupAlias },
        children,
        styleClass: isDirty ? "is-dirty" : undefined,
    };
}

function isTileOrTiles(nodeData: NodeData | NodegroupData | null) {
    if (!nodeData) return false;

    const tiles = Array.isArray(nodeData) ? nodeData : [nodeData];
    return tiles.every((tile) => "aliased_data" in tile);
}

function processTileData(
    tile: TileData,
    nodegroupAlias: string,
    tileDirtyStates: WidgetDirtyStates,
): TreeNode[] {
    if (!tile.aliased_data) {
        return [];
    }
    const tileValues = Object.entries(tile.aliased_data).reduce<TreeNode[]>(
        (accumulatedNodes, [childAlias, childData]) => {
            if (isTileOrTiles(childData)) {
                accumulatedNodes.push(
                    processNodegroup(
                        childAlias,
                        childData as TileData | TileData[],
                        tile.tileid,
                        tileDirtyStates,
                    ),
                );
            } else if (nodePresentationLookup.value[childAlias]?.visible) {
                accumulatedNodes.push(
                    processNode(
                        childAlias,
                        childData as NodeData | null,
                        tile.tileid,
                        nodegroupAlias,
                        tileDirtyStates,
                    ),
                );
            }
            return accumulatedNodes;
        },
        [],
    );

    return tileValues.sort((firstNode, secondNode) => {
        return (
            nodePresentationLookup.value[firstNode.data.alias].widget_order -
            nodePresentationLookup.value[secondNode.data.alias].widget_order
        );
    });
}

function extractAndOverrideDisplayValue(value: NodeData | null): string {
    if (!value?.display_value) {
        return $gettext("(Empty)");
    }
    if (value.display_value && value.display_value.includes("url_label")) {
        const urlPair = value.node_value as URLDetails;
        if (urlPair.url_label) {
            return urlPair.url_label;
        }
        return urlPair.url;
    }
    if (value.display_value) {
        return value.display_value;
    }
    return "";
}

function processNode(
    alias: string,
    data: NodeData | null,
    tileId: string | null,
    nodegroupAlias: string,
    tileDirtyStates: WidgetDirtyStates,
): TreeNode {
    const localizedLabel = $gettext("%{label}: %{labelData}", {
        label: nodePresentationLookup.value[alias].widget_label,
        labelData: extractAndOverrideDisplayValue(data),
    });

    return {
        key: generateStableKey(data),
        label: localizedLabel,
        data: {
            alias: alias,
            tileid: tileId,
            nodegroupAlias: nodegroupAlias,
        },
        styleClass: tileDirtyStates[alias] ? "is-dirty" : undefined,
    };
}

function createCardinalityNWrapper(
    nodegroupAlias: string,
    tiles: TileData[],
    parentTileId: string | null,
    widgetDirtyStates: WidgetDirtyStates,
): TreeNode {
    const childNodes = tiles.map((tile, index) => {
        const nodegroupDirtyStates = widgetDirtyStates[
            nodegroupAlias
        ] as WidgetDirtyStates;
        const tileDirtyStates = nodegroupDirtyStates[
            index
        ] as WidgetDirtyStates;

        const children = processTileData(
            tile,
            nodegroupAlias,
            tileDirtyStates.aliased_data as WidgetDirtyStates,
        );

        const hasDirtyChildren = children.some(
            (child) => child.styleClass === "is-dirty",
        );

        return {
            key: generateStableKey([tile, index]),
            label: children[0]?.label || $gettext("Empty"),
            data: { tileid: tile.tileid, alias: nodegroupAlias },
            children,
            styleClass: hasDirtyChildren ? "is-dirty" : undefined,
        };
    });

    const isDirty = childNodes.some(
        (childNode) => childNode.styleClass === "is-dirty",
    );

    return {
        key: generateStableKey([...tiles, parentTileId, nodegroupAlias]),
        label: nodePresentationLookup.value[nodegroupAlias].card_name,
        data: { tileid: parentTileId, alias: nodegroupAlias },
        children: childNodes,
        styleClass: isDirty ? "is-dirty" : undefined,
    };
}

function onCaretExpand(node: TreeNode) {
    const currentSelectedKey = Object.keys(selectedKeys.value)[0];
    if (node.key && node.key !== currentSelectedKey) {
        selectedKeys.value = { [node.key]: true };
        onNodeSelect(node);
    }
}

function onCaretCollapse(node: TreeNode) {
    const currentSelectedKey = Object.keys(selectedKeys.value)[0];
    if (node.key && node.key !== currentSelectedKey) {
        selectedKeys.value = { [node.key]: true };
    }
}

function onNodeSelect(treeNode: TreeNode) {
    let selectedTreeNodeAlias;
    if (!treeNode.data.nodegroupAlias) {
        selectedTreeNodeAlias = null;
    } else {
        selectedTreeNodeAlias = treeNode.data.alias;
    }

    setSelectedNodegroupAlias(
        treeNode.data.nodegroupAlias ?? treeNode.data.alias,
    );
    setSelectedTileId(treeNode.data.tileid);
    setSelectedNodeAlias(selectedTreeNodeAlias);

    const pathToSelectedTile = generateTilePath(
        resourceData,
        tree.value,
        treeNode.key,
    );

    if (pathToSelectedTile.at(-1) === selectedTreeNodeAlias) {
        pathToSelectedTile.pop();
    }
    if (pathToSelectedTile.at(-1) === "aliased_data") {
        pathToSelectedTile.pop();
    }

    setSelectedTilePath(pathToSelectedTile);
}

function onNodeUnselect() {
    setSelectedNodegroupAlias(null);
    setSelectedNodeAlias(null);
    setSelectedTileId(null);
    setSelectedTilePath(null);
}
</script>

<template>
    <div ref="treeContainerElement">
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
                @node-unselect="onNodeUnselect"
                @node-expand="onCaretExpand"
                @node-collapse="onCaretCollapse"
            />
        </Panel>
    </div>
</template>

<style scoped>
:deep(.is-dirty) {
    font-weight: bold;
    background-color: var(--p-yellow-100) !important;
}

:deep(.p-tree-node-content.p-tree-node-selected) {
    border: 0.125rem solid var(--p-form-field-border-color);
    color: var(--p-tree-node-color);
}
</style>
