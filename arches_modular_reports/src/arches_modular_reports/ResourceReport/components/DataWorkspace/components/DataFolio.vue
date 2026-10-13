<script setup lang="ts">
import { computed, ref } from "vue";
import { useGettext } from "vue3-gettext";

import Badge from "openvue/badge";
import Button from "openvue/button";
import Tag from "openvue/tag";

import { isAliasedNodeData } from "@/arches_vue_components/generics/GenericCard/utils.ts";
import { childNodegroupAliases } from "@/arches_modular_reports/ResourceReport/utils/graph-nodes.ts";
import {
    canAddTile,
    nodegroupTiles,
    tileSearchText,
    tileSummary,
} from "@/arches_modular_reports/ResourceReport/utils/tiles.ts";

import type {
    AliasedTileData,
    NodegroupWidgetConfig,
} from "@/arches_vue_components/types.ts";
import type {
    EditTileRequest,
    ResourceChangeSet,
} from "@/arches_modular_reports/ResourceReport/types.ts";

const EDIT_TILE = "edit-tile" as const;

const {
    nodegroupAlias,
    nodegroupWidgetConfigs,
    tiles,
    parentTileId,
    changeSet,
    filterText,
    selectedTileId,
} = defineProps<{
    nodegroupAlias: string;
    nodegroupWidgetConfigs: Record<string, NodegroupWidgetConfig>;
    tiles: AliasedTileData[];
    parentTileId: string | null;
    changeSet: ResourceChangeSet;
    filterText: string;
    selectedTileId: string | null;
}>();

const emit = defineEmits<{
    (event: typeof EDIT_TILE, editTileRequest: EditTileRequest): void;
}>();

const { $gettext } = useGettext();

const expandedTileIds = ref(new Set<string>());
const draggedTileId = ref<string | null>(null);

const nodegroupWidgetConfig = computed(
    () => nodegroupWidgetConfigs[nodegroupAlias],
);

const cardName = computed(() => nodegroupWidgetConfig.value.card?.name ?? "");

const visibleWidgets = computed(() =>
    nodegroupWidgetConfig.value.card_x_node_x_widgets.filter(
        (widget) => widget.visible,
    ),
);

const childAliases = computed(() =>
    childNodegroupAliases(nodegroupWidgetConfigs, nodegroupAlias),
);

const isParentPendingDelete = computed(
    () => parentTileId !== null && changeSet.isPendingDelete(parentTileId),
);

const isAddable = computed(
    () =>
        !isParentPendingDelete.value &&
        canAddTile(nodegroupWidgetConfig.value, tiles.length),
);

const cardinalityLabel = computed(() => {
    if (nodegroupWidgetConfig.value.cardinality === "n") {
        return "0..n";
    }
    return "0..1";
});

const normalizedFilterText = computed(() =>
    filterText.trim().toLocaleLowerCase(),
);

function tileIdOf(tile: AliasedTileData): string {
    return tile.tileid ?? "";
}

function displayValue(tile: AliasedTileData, nodeAlias: string): string {
    const nodeData = tile.aliased_data[nodeAlias];
    if (isAliasedNodeData(nodeData)) {
        return nodeData.display_value;
    }
    return "";
}

function tileLabel(tile: AliasedTileData): string {
    const summary = tileSummary(tile, nodegroupWidgetConfig.value);
    if (summary === "") {
        return $gettext("New entry");
    }
    return summary;
}

function changeTag(
    tile: AliasedTileData,
): { label: string; severity: "success" | "info" | "danger" } | null {
    const changeType = changeSet.changeTypeForTile(tileIdOf(tile));
    if (changeType === "add") {
        return { label: $gettext("New"), severity: "success" };
    }
    if (changeType === "edit") {
        return { label: $gettext("Edited"), severity: "info" };
    }
    if (changeType === "delete") {
        return { label: $gettext("Deleted"), severity: "danger" };
    }
    return null;
}

function isMarkedForDeletion(tile: AliasedTileData): boolean {
    return changeSet.changeTypeForTile(tileIdOf(tile)) === "delete";
}

function isLocked(tile: AliasedTileData): boolean {
    return (
        !nodegroupWidgetConfig.value.is_writable ||
        (changeSet.isPendingDelete(tileIdOf(tile)) &&
            !isMarkedForDeletion(tile))
    );
}

function matchesFilter(tile: AliasedTileData): boolean {
    if (!normalizedFilterText.value) {
        return false;
    }
    return visibleWidgets.value.some((widget) =>
        displayValue(tile, widget.node.alias)
            .toLocaleLowerCase()
            .includes(normalizedFilterText.value),
    );
}

function isExpanded(tile: AliasedTileData): boolean {
    if (expandedTileIds.value.has(tileIdOf(tile))) {
        return true;
    }
    return (
        normalizedFilterText.value !== "" &&
        tileSearchText(tile).includes(normalizedFilterText.value)
    );
}

function expandIcon(tile: AliasedTileData): string {
    if (isExpanded(tile)) {
        return "pi pi-chevron-down";
    }
    return "pi pi-chevron-right";
}

function toggleTile(tile: AliasedTileData): void {
    const tileId = tileIdOf(tile);
    if (expandedTileIds.value.has(tileId)) {
        expandedTileIds.value.delete(tileId);
    } else {
        expandedTileIds.value.add(tileId);
    }
}

async function addTile(): Promise<void> {
    const newTileId = await changeSet.addTile(nodegroupAlias, parentTileId);
    if (newTileId !== null) {
        emit(EDIT_TILE, { nodegroupAlias, tileId: newTileId });
    }
}

function editTile(tile: AliasedTileData): void {
    emit(EDIT_TILE, { nodegroupAlias, tileId: tileIdOf(tile) });
}

function deleteTile(tile: AliasedTileData): void {
    changeSet.deleteTile(nodegroupAlias, tileIdOf(tile));
}

function undoDelete(tile: AliasedTileData): void {
    changeSet.undoDelete(tileIdOf(tile));
}

function moveTileTo(tileId: string, targetIndex: number): void {
    const orderedTileIds = tiles.map(tileIdOf);
    const currentIndex = orderedTileIds.indexOf(tileId);
    if (
        currentIndex === targetIndex ||
        targetIndex < 0 ||
        targetIndex >= orderedTileIds.length
    ) {
        return;
    }
    orderedTileIds.splice(currentIndex, 1);
    orderedTileIds.splice(targetIndex, 0, tileId);
    changeSet.reorderTiles(nodegroupAlias, parentTileId, orderedTileIds);
}

function onDragStart(event: DragEvent, tile: AliasedTileData): void {
    draggedTileId.value = tileIdOf(tile);
    event.dataTransfer?.setData("text/plain", tileIdOf(tile));
}

function onDragOver(event: DragEvent): void {
    if (draggedTileId.value !== null) {
        event.preventDefault();
    }
}

function onDrop(targetIndex: number): void {
    if (draggedTileId.value !== null) {
        moveTileTo(draggedTileId.value, targetIndex);
    }
    draggedTileId.value = null;
}

function onDragEnd(): void {
    draggedTileId.value = null;
}
</script>

<template>
    <section class="data-folio">
        <header class="data-folio-header">
            <span class="data-folio-name">{{ cardName }}</span>
            <Badge
                v-if="tiles.length > 0"
                severity="secondary"
                :value="tiles.length"
            />
            <span class="data-folio-cardinality">{{ cardinalityLabel }}</span>
            <Button
                v-if="isAddable"
                class="data-folio-add"
                icon="pi pi-plus"
                variant="text"
                size="small"
                :label="$gettext('Add')"
                @click="addTile"
            />
        </header>
        <ul class="data-folio-tiles">
            <li
                v-for="(tile, tileIndex) in tiles"
                :key="tile.tileid ?? tileIndex"
                class="data-folio-tile"
                :class="{
                    'data-folio-tile-pending':
                        changeSet.changeTypeForTile(tileIdOf(tile)) !== null,
                    'data-folio-tile-deleted': changeSet.isPendingDelete(
                        tileIdOf(tile),
                    ),
                    'data-folio-tile-selected': selectedTileId === tile.tileid,
                    'data-folio-tile-match': matchesFilter(tile),
                }"
                @dragover="onDragOver"
                @drop="onDrop(tileIndex)"
            >
                <div
                    class="data-folio-tile-row"
                    :draggable="!isLocked(tile)"
                    @dragstart="onDragStart($event, tile)"
                    @dragend="onDragEnd"
                >
                    <Button
                        :icon="expandIcon(tile)"
                        variant="text"
                        size="small"
                        :aria-expanded="isExpanded(tile)"
                        :aria-label="$gettext('Show details')"
                        @click="toggleTile(tile)"
                    />
                    <div
                        v-if="!isLocked(tile)"
                        class="data-folio-reorder"
                    >
                        <i
                            class="pi pi-bars data-folio-drag-handle"
                            aria-hidden="true"
                        />
                        <Button
                            icon="pi pi-arrow-up"
                            variant="text"
                            size="small"
                            :aria-label="$gettext('Move up')"
                            :disabled="tileIndex === 0"
                            @click="moveTileTo(tileIdOf(tile), tileIndex - 1)"
                        />
                        <Button
                            icon="pi pi-arrow-down"
                            variant="text"
                            size="small"
                            :aria-label="$gettext('Move down')"
                            :disabled="tileIndex === tiles.length - 1"
                            @click="moveTileTo(tileIdOf(tile), tileIndex + 1)"
                        />
                    </div>
                    <span class="data-folio-summary">
                        {{ tileLabel(tile) }}
                    </span>
                    <Tag
                        v-if="changeTag(tile)"
                        :value="changeTag(tile)?.label"
                        :severity="changeTag(tile)?.severity"
                    />
                    <div
                        v-if="!isLocked(tile)"
                        class="data-folio-tile-actions"
                    >
                        <Button
                            v-if="isMarkedForDeletion(tile)"
                            icon="pi pi-undo"
                            variant="text"
                            size="small"
                            :label="$gettext('Undo delete')"
                            @click="undoDelete(tile)"
                        />
                        <template v-else>
                            <Button
                                icon="pi pi-pencil"
                                variant="text"
                                size="small"
                                :label="$gettext('Edit')"
                                @click="editTile(tile)"
                            />
                            <Button
                                icon="pi pi-trash"
                                variant="text"
                                size="small"
                                severity="danger"
                                :label="$gettext('Delete')"
                                @click="deleteTile(tile)"
                            />
                        </template>
                    </div>
                </div>
                <div
                    v-if="isExpanded(tile)"
                    class="data-folio-tile-body"
                >
                    <dl class="data-folio-fields">
                        <div
                            v-for="widget in visibleWidgets"
                            :key="widget.node.alias"
                            class="data-folio-field"
                        >
                            <dt>{{ widget.label }}</dt>
                            <dd>{{ displayValue(tile, widget.node.alias) }}</dd>
                        </div>
                    </dl>
                    <DataFolio
                        v-for="childAlias in childAliases"
                        :key="childAlias"
                        :nodegroup-alias="childAlias"
                        :nodegroup-widget-configs="nodegroupWidgetConfigs"
                        :tiles="nodegroupTiles(tile.aliased_data[childAlias])"
                        :parent-tile-id="tile.tileid"
                        :change-set="changeSet"
                        :filter-text="filterText"
                        :selected-tile-id="selectedTileId"
                        @edit-tile="emit(EDIT_TILE, $event)"
                    />
                </div>
            </li>
        </ul>
    </section>
</template>

<style scoped>
.data-folio {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
}

.data-folio-header {
    display: flex;
    align-items: center;
    gap: 0.8rem;
}

.data-folio-name {
    font-weight: 600;
}

.data-folio-cardinality {
    color: var(--p-text-muted-color);
    font-size: 1.2rem;
}

.data-folio-add {
    margin-inline-start: auto;
}

.data-folio-tiles {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    margin: 0;
    padding: 0;
    list-style: none;
}

.data-folio-tile {
    border: 0.1rem solid var(--p-content-border-color);
    border-radius: var(--p-content-border-radius);
}

.data-folio-tile-pending {
    background: var(--p-highlight-background);
}

.data-folio-tile-deleted .data-folio-summary {
    color: var(--p-text-muted-color);
    text-decoration: line-through;
}

.data-folio-tile-selected {
    border-color: var(--p-primary-color);
}

.data-folio-tile-match {
    box-shadow: inset 0.3rem 0 0 var(--p-primary-color);
}

.data-folio-tile-row {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    padding-inline-end: 0.4rem;
}

.data-folio-reorder {
    display: flex;
    align-items: center;
}

.data-folio-drag-handle {
    color: var(--p-text-muted-color);
    cursor: grab;
}

.data-folio-summary {
    flex: 1;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.data-folio-tile-actions {
    display: flex;
    gap: 0.2rem;
}

.data-folio-tile-body {
    display: flex;
    flex-direction: column;
    gap: 0.8rem;
    padding-block: 0.4rem 0.8rem;
    padding-inline: 1.8rem 0.8rem;
}

.data-folio-fields {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    margin: 0;
}

.data-folio-field {
    display: flex;
    gap: 0.8rem;
}

.data-folio-field dt {
    min-width: 14rem;
    color: var(--p-text-muted-color);
}

.data-folio-field dd {
    margin: 0;
}
</style>
