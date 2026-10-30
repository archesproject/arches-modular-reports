<script setup lang="ts">
import { computed } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";
import Message from "openvue/message";
import Tag from "openvue/tag";

import GenericWidget from "@/arches_vue_components/generics/GenericWidget/GenericWidget.vue";

import { VIEW } from "@/arches_vue_components/widgets/constants.ts";
import { useFolio } from "@/arches_modular_reports/ResourceReport/composables/useFolio.ts";
import { aliasedNodeDataOf } from "@/arches_modular_reports/ResourceReport/utils/tiles.ts";

import type {
    ComponentNode,
    FolioConfig,
} from "@/arches_modular_reports/ResourceReport/types.ts";

const { component } = defineProps<{
    component: ComponentNode<FolioConfig>;
}>();

const { $gettext } = useGettext();
const {
    reportData,
    hasNodegroup,
    nodegroupWidgetConfig,
    cardName,
    tiles,
    isAddable,
    isFlashed,
    isEditableTile,
    isMarkedForDeletion,
    isPendingDelete,
    tileLabel,
    addTile,
    editTile,
    deleteTile,
    undoDelete,
    clearFlash,
} = useFolio(() => component);

const widget = computed(() =>
    nodegroupWidgetConfig.value.card_x_node_x_widgets.find(
        (candidateWidget) => candidateWidget.visible,
    ),
);

const tile = computed(() => {
    if (tiles.value.length === 0) {
        return null;
    }
    return tiles.value[0];
});

const nodeData = computed(() => {
    if (tile.value === null || widget.value === undefined) {
        return null;
    }
    const tileNodeData = aliasedNodeDataOf(tile.value, widget.value.node.alias);
    if (tileNodeData === null || tileNodeData.display_value === "") {
        return null;
    }
    return tileNodeData;
});

const isDeleted = computed(
    () => tile.value !== null && isPendingDelete(tile.value),
);
</script>

<template>
    <div
        ref="folio"
        class="field-folio"
        :class="{ 'field-folio-flash': isFlashed }"
        @animationend.self="clearFlash"
    >
        <Message
            v-if="!hasNodegroup"
            severity="error"
            size="small"
        >
            <span>
                {{
                    $gettext(
                        "This folio is missing a nodegroup this report can show.",
                    )
                }}
            </span>
        </Message>
        <template v-else>
            <span
                class="field-folio-label"
                :class="{ 'field-folio-deleted': isDeleted }"
            >
                {{ cardName }}
            </span>
            <div class="field-folio-value">
                <span :class="{ 'field-folio-deleted': isDeleted }">
                    <GenericWidget
                        v-if="nodeData !== null && widget !== undefined"
                        :aliased-node-data="nodeData"
                        :card-x-node-x-widget-data="widget"
                        :graph-slug="reportData.context.graph.slug"
                        :mode="VIEW"
                        :node-alias="widget.node.alias"
                        :should-show-label="false"
                    />
                    <span
                        v-else
                        class="field-folio-empty"
                    >
                        {{ $gettext("No value recorded.") }}
                    </span>
                </span>
                <template v-if="tile !== null && isEditableTile(tile)">
                    <Button
                        variant="link"
                        size="small"
                        :label="$gettext('Edit')"
                        :aria-label="
                            $gettext(
                                'Edit %{entry}',
                                { entry: tileLabel(tile) },
                                true,
                            )
                        "
                        @click="editTile(tile.tileid, widget?.node.alias)"
                    />
                    <Button
                        class="field-folio-delete"
                        variant="link"
                        size="small"
                        :label="$gettext('Delete')"
                        :aria-label="
                            $gettext(
                                'Delete %{entry}',
                                { entry: tileLabel(tile) },
                                true,
                            )
                        "
                        :disabled="reportData.changeSet.isBusy.value"
                        @click="deleteTile(tile.tileid)"
                    />
                </template>
                <template
                    v-else-if="tile !== null && isMarkedForDeletion(tile)"
                >
                    <Tag
                        severity="danger"
                        :value="$gettext('Deleted')"
                    />
                    <Button
                        icon="pi pi-undo"
                        variant="link"
                        size="small"
                        :label="$gettext('Undo delete')"
                        :aria-label="
                            $gettext(
                                'Undo deleting %{entry}',
                                { entry: tileLabel(tile) },
                                true,
                            )
                        "
                        :disabled="reportData.changeSet.isBusy.value"
                        @click="undoDelete(tile.tileid)"
                    />
                </template>
                <Button
                    v-else-if="isAddable"
                    variant="link"
                    size="small"
                    :label="$gettext('Add')"
                    :disabled="reportData.changeSet.isBusy.value"
                    @click="addTile"
                />
            </div>
        </template>
    </div>
</template>

<style scoped>
.field-folio {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    gap: 0.8rem;
    isolation: isolate;
    border-radius: var(--p-content-border-radius);
}

.field-folio-label {
    min-inline-size: 16rem;
    color: var(--p-text-muted-color);
}

.field-folio-value {
    display: flex;
    flex: 1;
    flex-wrap: wrap;
    align-items: baseline;
    gap: 0.8rem;
    min-inline-size: 0;
    font-weight: 500;
}

.field-folio-empty {
    color: var(--p-text-muted-color);
    font-style: italic;
    font-weight: 400;
}

.field-folio-deleted {
    opacity: 0.6;
    text-decoration: line-through;
}

.field-folio-delete,
.field-folio-delete:not(:disabled):hover,
.field-folio-delete:not(:disabled):active {
    color: var(--p-button-text-danger-color);
}

.field-folio-flash {
    animation: field-folio-flash 1.6s ease-out;
}

@keyframes field-folio-flash {
    from {
        background: var(--p-highlight-background);
        box-shadow: 0 0 0 0.8rem var(--p-highlight-background);
    }
}
</style>
