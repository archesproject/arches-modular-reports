<script setup lang="ts">
import { computed, inject, ref, useTemplateRef, watch } from "vue";
import { useGettext } from "vue3-gettext";

import Panel from "primevue/panel";
import Tree from "primevue/tree";
import Button from "primevue/button";

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

type SoftDeletePayload = {
    softDeleteKey: string;
    nodegroupValuePath: Array<string | number>;
    nextIsSoftDeleted: boolean;
};

const emit = defineEmits<{
    (eventName: "toggle-soft-delete", payload: SoftDeletePayload): void;
}>();

const { $gettext } = useGettext();

const CARDINALITY_N = "n";

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

const { requestCreateTile } = inject("createTile") as {
    requestCreateTile: (
        nodegroupAlias: string,
        nodegroupValuePath: Array<string | number>,
    ) => void;
};

const { resourceData, widgetDirtyStates, softDeletedTileKeys } = defineProps<{
    resourceData: ResourceData;
    widgetDirtyStates: WidgetDirtyStates;
    softDeletedTileKeys: Set<string>;
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
            ["aliased_data", nodegroupAlias],
            false,
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
            function (accumulatedExpandedKeys, node) {
                accumulatedExpandedKeys[node.key] = true;
                return accumulatedExpandedKeys;
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
    nodegroupValuePath: Array<string | number>,
    isSoftDeletedAncestor: boolean,
): TreeNode {
    if (Array.isArray(tileOrTiles)) {
        return createCardinalityNWrapper(
            nodegroupAlias,
            tileOrTiles,
            parentTileId,
            widgetDirtyStates,
            nodegroupValuePath,
            isSoftDeletedAncestor,
        );
    }

    const softDeleteKey =
        tileOrTiles.tileid ?? JSON.stringify(nodegroupValuePath);

    const isSoftDeletedSelf = softDeletedTileKeys.has(softDeleteKey);
    const isSoftDeleted = isSoftDeletedAncestor || isSoftDeletedSelf;

    const tileDirtyStates = (
        widgetDirtyStates?.[nodegroupAlias] as WidgetDirtyStates
    )?.aliased_data;

    const children = processTileData(
        tileOrTiles,
        nodegroupAlias,
        tileDirtyStates as WidgetDirtyStates,
        nodegroupValuePath,
        isSoftDeleted,
    );

    const styleClassParts = [];
    if (isSoftDeleted) {
        styleClassParts.push("is-soft-deleted");
    }

    const hasDirtyDescendants = children.some((childNode) =>
        childNode.styleClass?.includes("is-dirty"),
    );
    const hasSoftDeletedDescendants =
        !isSoftDeleted &&
        children.some((childNode) =>
            childNode.styleClass?.includes("is-soft-deleted"),
        );

    const isDirty = hasDirtyDescendants || hasSoftDeletedDescendants;
    if (isDirty) {
        styleClassParts.push("is-dirty");
    }

    return {
        key: generateStableKey(tileOrTiles),
        label: nodePresentationLookup.value[nodegroupAlias].card_name,
        data: {
            tileid: tileOrTiles.tileid,
            alias: nodegroupAlias,
            cardinality:
                nodePresentationLookup.value[nodegroupAlias].nodegroup
                    .cardinality,
            nodegroupValuePath,
            softDeleteKey,
            isSoftDeleted,
        },
        children: children,
        styleClass:
            styleClassParts.length > 0 ? styleClassParts.join(" ") : undefined,
    } as TreeNode;
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
    tileValuePath: Array<string | number>,
    isSoftDeletedAncestor: boolean,
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
                        [...tileValuePath, "aliased_data", childAlias],
                        isSoftDeletedAncestor,
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
                        isSoftDeletedAncestor,
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

function convertRichHtmlToPlainText(htmlInput: string): string {
    if (!htmlInput) {
        return "";
    }

    const parser = new DOMParser();
    const documentResult = parser.parseFromString(htmlInput, "text/html");

    const rawTextContent = documentResult.body.textContent ?? "";

    return rawTextContent.replace(/\s+/g, " ").trim();
}

function processNode(
    alias: string,
    data: NodeData | null,
    tileId: string | null,
    nodegroupAlias: string,
    tileDirtyStates: WidgetDirtyStates,
    isSoftDeletedAncestor: boolean,
): TreeNode {
    const isEmpty = !data || !data?.display_value;
    const isRichText = nodePresentationLookup.value[alias].is_rich_text;
    const label = $gettext(nodePresentationLookup.value[alias].widget_label);
    const nodeValueClass = isEmpty ? "is-empty" : "has-value";

    let nodeValue = extractAndOverrideDisplayValue(data);
    if (isRichText) {
        nodeValue = convertRichHtmlToPlainText(nodeValue);
    }
    nodeValue =
        nodeValue.length > 50 ? nodeValue.slice(0, 47) + "..." : nodeValue;

    const styleClassParts = [];

    if (isSoftDeletedAncestor) {
        styleClassParts.push("is-soft-deleted");
    }

    const isDirty = Boolean(tileDirtyStates[alias]);
    if (isDirty) {
        styleClassParts.push("is-dirty");
    }

    return {
        key: generateStableKey(data),
        label: label,
        data: {
            alias: alias,
            tileid: tileId,
            nodegroupAlias: nodegroupAlias,
            nodeValue: nodeValue,
            nodeValueClass: nodeValueClass,
            isRequired: nodePresentationLookup.value[alias].is_required,
            isSoftDeleted: isSoftDeletedAncestor,
        },
        styleClass:
            styleClassParts.length > 0 ? styleClassParts.join(" ") : undefined,
    } as TreeNode;
}

function createCardinalityNWrapper(
    nodegroupAlias: string,
    tiles: TileData[],
    parentTileId: string | null,
    widgetDirtyStates: WidgetDirtyStates,
    nodegroupValuePath: Array<string | number>,
    isSoftDeletedAncestor: boolean,
): TreeNode {
    const wrapperSoftDeleteKey = JSON.stringify(nodegroupValuePath);
    const isWrapperSoftDeleted =
        isSoftDeletedAncestor || softDeletedTileKeys.has(wrapperSoftDeleteKey);

    const childNodes = tiles.map((tile, index) => {
        const tileValuePath = [...nodegroupValuePath, index];

        const tileSoftDeleteKey = tile.tileid ?? JSON.stringify(tileValuePath);
        const isTileSoftDeleted =
            isWrapperSoftDeleted || softDeletedTileKeys.has(tileSoftDeleteKey);

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
            tileValuePath,
            isTileSoftDeleted,
        );

        const styleClassParts = [];

        if (isTileSoftDeleted) {
            styleClassParts.push("is-soft-deleted");
        }

        const hasDirtyChildren = children.some((childNode) =>
            childNode.styleClass?.includes("is-dirty"),
        );
        const hasSoftDeletedChildren =
            !isTileSoftDeleted &&
            children.some((childNode) =>
                childNode.styleClass?.includes("is-soft-deleted"),
            );

        const isDirty = hasDirtyChildren || hasSoftDeletedChildren;
        if (isDirty) {
            styleClassParts.push("is-dirty");
        }

        return {
            key: generateStableKey([tile, index]),
            label: children[0]?.label || $gettext("Empty"),
            data: {
                tileid: tile.tileid,
                alias: nodegroupAlias,
                cardinality:
                    nodePresentationLookup.value[nodegroupAlias].nodegroup
                        .cardinality,
                nodegroupValuePath: tileValuePath,
                softDeleteKey: tileSoftDeleteKey,
                isSoftDeleted: isTileSoftDeleted,
            },
            children,
            styleClass:
                styleClassParts.length > 0
                    ? styleClassParts.join(" ")
                    : undefined,
        } as TreeNode;
    });

    const styleClassParts = [];

    if (isWrapperSoftDeleted) {
        styleClassParts.push("is-soft-deleted");
    }

    const hasDirtyDescendants = childNodes.some((childNode) => {
        return childNode.styleClass?.includes("is-dirty");
    });
    const hasSoftDeletedDescendants =
        !isWrapperSoftDeleted &&
        childNodes.some((childNode) =>
            childNode.styleClass?.includes("is-soft-deleted"),
        );

    const isDirty = hasDirtyDescendants || hasSoftDeletedDescendants;
    if (isDirty) {
        styleClassParts.push("is-dirty");
    }

    return {
        key: generateStableKey([...tiles, parentTileId, nodegroupAlias]),
        label: nodePresentationLookup.value[nodegroupAlias].card_name,
        data: {
            tileid: parentTileId,
            alias: nodegroupAlias,
            cardinality:
                nodePresentationLookup.value[nodegroupAlias].nodegroup
                    .cardinality,
            nodegroupValuePath,
            softDeleteKey: wrapperSoftDeleteKey,
            isSoftDeleted: isWrapperSoftDeleted,
        },
        children: childNodes,
        styleClass:
            styleClassParts.length > 0 ? styleClassParts.join(" ") : undefined,
    } as TreeNode;
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

function onAddNewTile(treeNode: TreeNode) {
    const treeNodeData = treeNode.data;

    const nodegroupValuePath =
        treeNodeData.nodegroupValuePath ??
        generateTilePath(resourceData, tree.value, treeNode.key);

    setSelectedNodegroupAlias(treeNodeData.alias);
    setSelectedNodeAlias(null);
    setSelectedTileId(null);

    requestCreateTile(treeNodeData.alias, nodegroupValuePath);
}

function onSoftDelete(treeNode: TreeNode) {
    const nodegroupValuePath =
        treeNode.data.nodegroupValuePath ??
        generateTilePath(resourceData, tree.value, treeNode.key);

    const softDeleteKey =
        treeNode.data.softDeleteKey ??
        treeNode.data.tileid ??
        JSON.stringify(nodegroupValuePath);

    emit("toggle-soft-delete", {
        softDeleteKey,
        nodegroupValuePath,
        nextIsSoftDeleted: true,
    });
}

function onRestore(treeNode: TreeNode) {
    const nodegroupValuePath =
        treeNode.data.nodegroupValuePath ??
        generateTilePath(resourceData, tree.value, treeNode.key);

    const softDeleteKey =
        treeNode.data.softDeleteKey ??
        treeNode.data.tileid ??
        JSON.stringify(nodegroupValuePath);

    emit("toggle-soft-delete", {
        softDeleteKey,
        nodegroupValuePath,
        nextIsSoftDeleted: false,
    });
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
            >
                <template #default="slotProps">
                    <div
                        style="display: flex; align-items: center; gap: 0.5rem"
                    >
                        <div style="margin-inline-end: 0.5rem">
                            <span
                                :class="{
                                    'is-soft-deleted-text': Boolean(
                                        slotProps.node.data.isSoftDeleted,
                                    ),
                                }"
                            >
                                <span>{{ slotProps.node.label }}</span>
                                <span
                                    v-if="slotProps.node.data.isRequired"
                                    class="is-required"
                                    >*</span
                                >
                                <span>:</span>
                            </span>
                        </div>

                        <Button
                            v-if="
                                slotProps.node.data.cardinality == CARDINALITY_N
                            "
                            icon="pi pi-plus"
                            size="small"
                            rounded
                            variant="outlined"
                            :disabled="
                                Boolean(slotProps.node.data.isSoftDeleted)
                            "
                            :aria-label="$gettext('Add new tile')"
                            @click.stop="onAddNewTile(slotProps.node)"
                        />

                        <template
                            v-if="slotProps.node.data.nodegroupAlias == null"
                        >
                            <Button
                                v-if="!slotProps.node.data.isSoftDeleted"
                                icon="pi pi-trash"
                                size="small"
                                rounded
                                variant="outlined"
                                severity="danger"
                                :aria-label="$gettext('Delete')"
                                @click.stop="onSoftDelete(slotProps.node)"
                            />
                            <Button
                                v-else
                                icon="pi pi-undo"
                                size="small"
                                rounded
                                severity="info"
                                :aria-label="$gettext('Restore')"
                                @click.stop="onRestore(slotProps.node)"
                            />
                        </template>

                        <span
                            v-if="slotProps.node.data.nodegroupAlias != null"
                            :class="[
                                slotProps.node.data.nodeValueClass,
                                {
                                    'is-soft-deleted-text': Boolean(
                                        slotProps.node.data.isSoftDeleted,
                                    ),
                                },
                            ]"
                        >
                            {{ slotProps.node.data.nodeValue }}
                        </span>
                    </div>
                </template>
            </Tree>
        </Panel>
    </div>
</template>

<style scoped>
.is-soft-deleted-text {
    text-decoration: line-through;
}

:deep(.p-tree-node-content.is-soft-deleted:not(.p-tree-node-selected)) {
    background-color: var(--p-red-100) !important;
}

:deep(
        .p-tree-node.is-soft-deleted
            > .p-tree-node-content:not(.p-tree-node-selected)
    ) {
    background-color: var(--p-red-100) !important;
}

:deep(
        .p-tree-node-content.is-dirty:not(.p-tree-node-selected):not(
                .is-soft-deleted
            )
    ) {
    font-weight: bold;
    background-color: var(--p-yellow-100) !important;
}

:deep(
        .p-tree-node.is-dirty
            > .p-tree-node-content:not(.p-tree-node-selected):not(
                .is-soft-deleted
            )
    ) {
    font-weight: bold;
    background-color: var(--p-yellow-100) !important;
}

:deep(.is-empty) {
    font-weight: normal;
    font-style: italic;
}
:deep(.has-value) {
    font-weight: bold;
}
:deep(.is-required) {
    font-weight: bold;
    color: var(--p-red-600);
    margin-inline: 0.25rem;
}

:deep(.p-tree-node-content.p-tree-node-selected) {
    border: 0.125rem solid var(--p-form-field-border-color);
    color: var(--p-tree-node-color);
}
</style>
