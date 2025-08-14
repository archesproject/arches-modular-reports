<script setup lang="ts">
import {
    computed,
    inject,
    onBeforeUnmount,
    onMounted,
    ref,
    useTemplateRef,
    watch,
} from "vue";
import { useGettext } from "vue3-gettext";

import Panel from "primevue/panel";
import Tree from "primevue/tree";

import { findNodeInTree } from "@/arches_modular_reports/ModularReport/utils.ts";

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

const selectedNodeAlias = defineModel<string | null>("selected-node-alias");

const { resourceData, widgetDirtyStates } = defineProps<{
    resourceData: ResourceData;
    widgetDirtyStates: WidgetDirtyStates;
}>();

const treeContainerElement = useTemplateRef("treeContainerElement");

const selectedKeys: Ref<TreeSelectionKeys> = ref({});
const expandedKeys: Ref<TreeExpandedKeys> = ref({});

const { selectedNodegroupAlias, setSelectedNodegroupAlias } = inject<{
    selectedNodegroupAlias: Ref<string>;
    setSelectedNodegroupAlias: (nodegroupAlias: string | null) => void;
}>("selectedNodegroupAlias")!;
const { selectedTileId, setSelectedTileId } = inject<{
    selectedTileId: Ref<string | null>;
    setSelectedTileId: (tileId: string | null | undefined) => void;
}>("selectedTileId")!;
const nodePresentationLookup = inject<Ref<NodePresentationLookup>>(
    "nodePresentationLookup",
)!;

onMounted(() => {
    document.addEventListener("pointerdown", handleExternalPointerDown);
});

onBeforeUnmount(() => {
    document.removeEventListener("pointerdown", handleExternalPointerDown);
});

const tree = computed(() => {
    const topCards = Object.entries(resourceData.aliased_data).reduce<
        TreeNode[]
    >((accumulatedNodes, [alias, data]) => {
        accumulatedNodes.push(
            processNodegroup(alias, data as TileData | TileData[], null),
        );
        return accumulatedNodes;
    }, []);
    return topCards.sort((first, second) => {
        return (
            nodePresentationLookup.value[first.data.alias].card_order -
            nodePresentationLookup.value[second.data.alias].card_order
        );
    });
});

watch(
    [selectedTileId, selectedNodegroupAlias, selectedNodeAlias],
    () => {
        const { found, path } = findNodeInTree(
            tree.value,
            selectedTileId.value,
            selectedNodegroupAlias.value,
        );
        if (!found) {
            return;
        }

        const nextExpandedKeys: TreeExpandedKeys = { ...expandedKeys.value };
        for (const ancestorNode of path) {
            nextExpandedKeys[ancestorNode.key as string | number] = true;
        }
        nextExpandedKeys[found.key as string | number] = true;
        expandedKeys.value = nextExpandedKeys;

        if (!selectedNodeAlias.value) {
            return;
        }

        const targetChild = found.children?.find(
            (childNode) => childNode.data.alias === selectedNodeAlias.value,
        );
        if (!targetChild?.key) {
            return;
        }

        const newSelectedKey = String(targetChild.key);
        const currentSelectedKey = Object.keys(selectedKeys.value)[0];

        if (currentSelectedKey !== newSelectedKey) {
            selectedKeys.value = { [newSelectedKey]: true };
        }
    },
    { flush: "post" },
);

function getBooleanAtPath(
    root: WidgetDirtyStates,
    ...pathSegments: Array<string | null>
): boolean {
    let current: boolean | WidgetDirtyStates = root;

    for (const pathSegment of pathSegments) {
        if (!pathSegment || typeof current !== "object") {
            return false;
        }

        current = current[pathSegment];
    }
    return current === true;
}

function handleExternalPointerDown(event: PointerEvent) {
    const rootElement = treeContainerElement.value;
    const eventTargetNode = event.target as Node | null;

    if (
        !rootElement ||
        (eventTargetNode && rootElement.contains(eventTargetNode))
    ) {
        return;
    }

    selectedKeys.value = {};
}

function processTileData(tile: TileData, nodegroupAlias: string): TreeNode[] {
    const tileValues = Object.entries(tile.aliased_data).reduce<TreeNode[]>(
        (accumulatedNodes, [alias, data]) => {
            if (isTileOrTiles(data)) {
                accumulatedNodes.push(
                    processNodegroup(
                        alias,
                        data as TileData | TileData[],
                        tile.tileid,
                    ),
                );
            } else if (nodePresentationLookup.value[alias].visible) {
                accumulatedNodes.push(
                    processNode(
                        alias,
                        data as NodeData | null,
                        tile.tileid,
                        nodegroupAlias,
                    ),
                );
            }
            return accumulatedNodes;
        },
        [],
    );
    return tileValues.sort((first, second) => {
        return (
            nodePresentationLookup.value[first.data.alias].widget_order -
            nodePresentationLookup.value[second.data.alias].widget_order
        );
    });
}

function processNode(
    alias: string,
    data: NodeData | null,
    tileId: string | null,
    nodegroupAlias: string,
): TreeNode {
    const isDirty = getBooleanAtPath(
        widgetDirtyStates,
        nodegroupAlias,
        tileId ?? "null",
        alias,
    );

    const localizedLabel = $gettext("%{label}: %{labelData}", {
        label: nodePresentationLookup.value[alias].widget_label,
        labelData: extractAndOverrideDisplayValue(data),
    });

    return {
        key: `${alias}-node-value-for-${tileId}`,
        label: localizedLabel,
        data: { alias: alias, tileid: tileId, nodegroupAlias },
        styleClass: isDirty ? "is-dirty" : undefined,
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
        const children = processTileData(tileOrTiles, nodegroupAlias);

        const isDirty = children.some((child) => {
            return getBooleanAtPath(
                widgetDirtyStates,
                nodegroupAlias,
                child.data.tileid ?? "null",
                child.data.alias,
            );
        });

        return {
            key: `${nodegroupAlias}-child-of-${parentTileId}`,
            label: nodePresentationLookup.value[nodegroupAlias].card_name,
            data: { tileid: tileOrTiles.tileid, alias: nodegroupAlias },
            children: children,
            styleClass: isDirty ? "is-dirty" : undefined,
        };
    }
}

function createCardinalityNWrapper(
    nodegroupAlias: string,
    tiles: TileData[],
    parentTileId: string | null,
): TreeNode {
    let isDirty = false;

    return {
        key: `${nodegroupAlias}-child-of-${parentTileId}`,
        label: nodePresentationLookup.value[nodegroupAlias].card_name,
        data: { tileid: parentTileId, alias: nodegroupAlias },
        children: tiles.map((tile, indexWithinGroup) => {
            const children = processTileData(tile, nodegroupAlias);
            const hasDirtyChildren = children.some(
                (child) => child.styleClass === "is-dirty",
            );

            isDirty = isDirty || hasDirtyChildren;

            const tileNode: TreeNode = {
                key: tile.tileid!,
                label: indexWithinGroup.toString(),
                data: { tileid: tile.tileid, alias: nodegroupAlias },
                children: children,
                styleClass: hasDirtyChildren ? "is-dirty" : undefined,
            };
            tileNode.label = tileNode.children?.[0]?.label as string;

            return tileNode;
        }),
        styleClass: isDirty ? "is-dirty" : undefined,
    };
}

function extractAndOverrideDisplayValue(value: NodeData | null): string {
    if (value === null) {
        return $gettext("(Empty)");
    }
    if (value.display_value && value.display_value.includes("url_label")) {
        const urlPair = value.node_value as URLDetails;
        return urlPair.url_label || urlPair.url;
    }
    return value.display_value ?? "";
}

function isTileOrTiles(nodeData: NodeData | NodegroupData | null) {
    const tiles = Array.isArray(nodeData) ? nodeData : [nodeData];
    return tiles.every((tile) => (tile as TileData)?.aliased_data);
}

function onNodeSelect(node: TreeNode) {
    if (!node.data.nodegroupAlias) {
        selectedNodeAlias.value = null;
    } else {
        selectedNodeAlias.value = node.data.alias;
    }

    setSelectedNodegroupAlias(node.data.nodegroupAlias ?? node.data.alias);
    setSelectedTileId(node.data.tileid);
}

function onNodeUnselect() {
    selectedNodeAlias.value = null;
    // TODO: re-enable this when panel show/hide is not tied to it
    // setSelectedNodegroupAlias(null);
    setSelectedTileId(null);
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
