<script setup lang="ts">
import { inject } from "vue";

import type { Ref } from "vue";
import type { NodePresentationLookup } from "@/arches_provenance/EditableReport/types";

const { selectedNodeAlias } = inject("selectedNodeAlias") as {
    selectedNodeAlias: string | null;
};
const { selectedTileId } = inject("selectedTileId") as {
    selectedTileId: string | null;
};
const nodePresentationLookup = inject<Ref<NodePresentationLookup>>(
    "nodePresentationLookup",
)!;
</script>

<template>
    <p>Selected Node: {{ selectedNodeAlias }}</p>
    <p v-if="selectedNodeAlias">
        Datatype: {{ nodePresentationLookup[selectedNodeAlias].datatype }}
    </p>
    <p>Selected Tile: {{ selectedTileId }}</p>
</template>
