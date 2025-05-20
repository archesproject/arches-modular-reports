<script setup lang="ts">
import { inject, ref } from "vue";
import { useGettext } from "vue3-gettext";

import Panel from "primevue/panel";
import Tree from "primevue/tree";

import type { Ref } from "vue";
import type { TreeExpandedKeys, TreeSelectionKeys } from "primevue/tree";
import type { TreeNode } from "primevue/treenode";

const { $gettext } = useGettext();

const tree: TreeNode[] = []; // todo
const selectedKeys: Ref<TreeSelectionKeys> = ref({});
const expandedKeys: Ref<TreeExpandedKeys> = ref({});
const { setSelectedTileId } = inject("selectedTileId") as {
    setSelectedTileId: (tileId: string | null) => void;
};

function onNodeSelect(node: TreeNode) {
    setSelectedTileId(node.data.tileId);
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
