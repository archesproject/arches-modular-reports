<script setup lang="ts">
import { inject, useTemplateRef } from "vue";

import Button from "primevue/button";

import DefaultCard from "@/arches_component_lab/cards/DefaultCard/DefaultCard.vue";

import { EDIT } from "@/arches_component_lab/widgets/constants.ts";

const graphSlug = inject<string>("graphSlug");
const resourceInstanceId = inject<string>("resourceInstanceId");

const defaultCard = useTemplateRef("defaultCard");

const { selectedNodegroupAlias } = inject("selectedNodegroupAlias") as {
    selectedNodegroupAlias: string | null;
};
const { selectedTileId } = inject("selectedTileId") as {
    selectedTileId: string | null | undefined;
};

const emit = defineEmits(["save"]);

async function save() {
    if (defaultCard.value) {
        await defaultCard.value.save();
    }
}
</script>

<template>
    <DefaultCard
        v-if="selectedNodegroupAlias && graphSlug"
        ref="defaultCard"
        :mode="EDIT"
        :nodegroup-alias="selectedNodegroupAlias"
        :graph-slug="graphSlug"
        :resource-instance-id="resourceInstanceId"
        :should-show-form-buttons="false"
        :tile-id="selectedTileId"
        @save="
            console.log('save', $event);
            emit('save', $event);
        "
        @update:widget-dirty-states="
            console.log('update:widgetDirtyStates', $event)
        "
        @update:tile-data="console.log('update:tileData', $event)"
    />

    <Button
        class="p-button-secondary"
        label="Save"
        @click="save"
    />
</template>
