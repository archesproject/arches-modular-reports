<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useGettext } from "vue3-gettext";

import Badge from "openvue/badge";
import Button from "openvue/button";
import Tag from "openvue/tag";

import { childNodegroupAliases } from "@/arches_modular_reports/ResourceReport/utils/graph-nodes.ts";
import {
    aliasedNodeDataOf,
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
const collapsedTileIds = ref(new Set<string>());
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

const isAddable = computed(() =>
    canAddTile(
        nodegroupWidgetConfig.value,
        tiles.length,
        parentTileId,
        changeSet,
    ),
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

const tileRows = computed(() =>
    tiles.map((tile, tileIndex) => {
        const tileId = tile.tileid ?? "";
        const isMarkedForDeletion =
            changeSet.changeTypeForTile(tileId) === "delete";
        const isPendingDelete = changeSet.isPendingDelete(tileId);
        return {
            tile,
            tileId,
            tileIndex,
            label: tileLabel(tile),
            changeTag: changeTag(tileId),
            isMarkedForDeletion,
            isPendingDelete,
            isLocked:
                !nodegroupWidgetConfig.value.is_writable ||
                (isPendingDelete && !isMarkedForDeletion),
            isHighlighted: matchesFilter(tile),
            isExpanded: isExpanded(tileId, tile),
        };
    }),
);

watch(normalizedFilterText, () => {
    collapsedTileIds.value = new Set();
});

function displayValue(tile: AliasedTileData, nodeAlias: string): string {
    return aliasedNodeDataOf(tile, nodeAlias)?.display_value ?? "";
}

function tileLabel(tile: AliasedTileData): string {
    const summary = tileSummary(tile, nodegroupWidgetConfig.value);
    if (summary === "") {
        return $gettext("New entry");
    }
    return summary;
}

function changeTag(
    tileId: string,
): { label: string; severity: "success" | "info" | "danger" } | null {
    const changeType = changeSet.changeTypeForTile(tileId);
    if (changeType === "add") {
        return { label: $gettext("Added"), severity: "success" };
    }
    if (changeType === "edit") {
        return { label: $gettext("Edited"), severity: "info" };
    }
    if (changeType === "delete") {
        return { label: $gettext("Deleted"), severity: "danger" };
    }
    return null;
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

function isExpanded(tileId: string, tile: AliasedTileData): boolean {
    if (collapsedTileIds.value.has(tileId)) {
        return false;
    }
    if (expandedTileIds.value.has(tileId)) {
        return true;
    }
    return (
        normalizedFilterText.value !== "" &&
        tileSearchText(tile).includes(normalizedFilterText.value)
    );
}

function expandIcon(isTileExpanded: boolean): string {
    if (isTileExpanded) {
        return "pi pi-chevron-down";
    }
    return "pi pi-chevron-right";
}

function toggleTile(tileId: string, isTileExpanded: boolean): void {
    if (isTileExpanded) {
        expandedTileIds.value.delete(tileId);
        collapsedTileIds.value.add(tileId);
    } else {
        collapsedTileIds.value.delete(tileId);
        expandedTileIds.value.add(tileId);
    }
}

async function addTile(): Promise<void> {
    const newTileId = await changeSet.addTile(nodegroupAlias, parentTileId);
    if (newTileId !== null) {
        emit(EDIT_TILE, { nodegroupAlias, tileId: newTileId });
    }
}

function editTile(tileId: string): void {
    emit(EDIT_TILE, { nodegroupAlias, tileId });
}

function deleteTile(tileId: string): void {
    changeSet.deleteTile(nodegroupAlias, tileId);
}

function undoDelete(tileId: string): void {
    changeSet.undoDelete(tileId);
}

function moveTileTo(tileId: string, targetIndex: number): void {
    const orderedTileIds = tileRows.value.map((tileRow) => tileRow.tileId);
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

function onDragStart(event: DragEvent, tileId: string): void {
    draggedTileId.value = tileId;
    event.dataTransfer?.setData("text/plain", tileId);
}

function onDragOver(event: DragEvent): void {
    if (draggedTileId.value !== null) {
        event.preventDefault();
    }
}

function onDrop(event: DragEvent, targetIndex: number): void {
    event.preventDefault();
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
                :disabled="changeSet.isBusy.value"
                @click="addTile"
            />
        </header>
        <ul class="data-folio-tiles">
            <li
                v-for="tileRow in tileRows"
                :key="tileRow.tileId"
                class="data-folio-tile"
                :class="{
                    'data-folio-tile-pending': tileRow.changeTag !== null,
                    'data-folio-tile-deleted': tileRow.isPendingDelete,
                    'data-folio-tile-selected':
                        selectedTileId === tileRow.tileId,
                    'data-folio-tile-match': tileRow.isHighlighted,
                }"
                @dragover="onDragOver"
                @drop="onDrop($event, tileRow.tileIndex)"
            >
                <div
                    class="data-folio-tile-row"
                    :draggable="!tileRow.isLocked && !changeSet.isBusy.value"
                    @dragstart="onDragStart($event, tileRow.tileId)"
                    @dragend="onDragEnd"
                >
                    <Button
                        variant="text"
                        size="small"
                        :icon="expandIcon(tileRow.isExpanded)"
                        :aria-expanded="tileRow.isExpanded"
                        :aria-label="
                            $gettext(
                                'Show details for %{entry}',
                                {
                                    entry: tileRow.label,
                                },
                                true,
                            )
                        "
                        @click="toggleTile(tileRow.tileId, tileRow.isExpanded)"
                    />
                    <div
                        v-if="!tileRow.isLocked"
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
                            :aria-label="
                                $gettext(
                                    'Move %{entry} up',
                                    {
                                        entry: tileRow.label,
                                    },
                                    true,
                                )
                            "
                            :disabled="
                                tileRow.tileIndex === 0 ||
                                changeSet.isBusy.value
                            "
                            @click="
                                moveTileTo(
                                    tileRow.tileId,
                                    tileRow.tileIndex - 1,
                                )
                            "
                        />
                        <Button
                            icon="pi pi-arrow-down"
                            variant="text"
                            size="small"
                            :aria-label="
                                $gettext(
                                    'Move %{entry} down',
                                    {
                                        entry: tileRow.label,
                                    },
                                    true,
                                )
                            "
                            :disabled="
                                tileRow.tileIndex === tiles.length - 1 ||
                                changeSet.isBusy.value
                            "
                            @click="
                                moveTileTo(
                                    tileRow.tileId,
                                    tileRow.tileIndex + 1,
                                )
                            "
                        />
                    </div>
                    <span class="data-folio-summary">
                        {{ tileRow.label }}
                    </span>
                    <Tag
                        v-if="tileRow.changeTag"
                        :value="tileRow.changeTag.label"
                        :severity="tileRow.changeTag.severity"
                    />
                    <div
                        v-if="!tileRow.isLocked"
                        class="data-folio-tile-actions"
                    >
                        <Button
                            v-if="tileRow.isMarkedForDeletion"
                            icon="pi pi-undo"
                            variant="text"
                            size="small"
                            :label="$gettext('Undo delete')"
                            :aria-label="
                                $gettext(
                                    'Undo deleting %{entry}',
                                    {
                                        entry: tileRow.label,
                                    },
                                    true,
                                )
                            "
                            :disabled="changeSet.isBusy.value"
                            @click="undoDelete(tileRow.tileId)"
                        />
                        <template v-else>
                            <Button
                                icon="pi pi-pencil"
                                variant="text"
                                size="small"
                                :label="$gettext('Edit')"
                                :aria-label="
                                    $gettext(
                                        'Edit %{entry}',
                                        {
                                            entry: tileRow.label,
                                        },
                                        true,
                                    )
                                "
                                @click="editTile(tileRow.tileId)"
                            />
                            <Button
                                icon="pi pi-trash"
                                variant="text"
                                size="small"
                                severity="danger"
                                :label="$gettext('Delete')"
                                :aria-label="
                                    $gettext(
                                        'Delete %{entry}',
                                        {
                                            entry: tileRow.label,
                                        },
                                        true,
                                    )
                                "
                                :disabled="changeSet.isBusy.value"
                                @click="deleteTile(tileRow.tileId)"
                            />
                        </template>
                    </div>
                </div>
                <div
                    v-if="tileRow.isExpanded"
                    class="data-folio-tile-body"
                >
                    <dl class="data-folio-fields">
                        <div
                            v-for="widget in visibleWidgets"
                            :key="widget.node.alias"
                            class="data-folio-field"
                        >
                            <dt>{{ widget.label }}</dt>
                            <dd>
                                {{
                                    displayValue(
                                        tileRow.tile,
                                        widget.node.alias,
                                    )
                                }}
                            </dd>
                        </div>
                    </dl>
                    <DataFolio
                        v-for="childAlias in childAliases"
                        :key="childAlias"
                        :nodegroup-alias="childAlias"
                        :nodegroup-widget-configs="nodegroupWidgetConfigs"
                        :tiles="
                            nodegroupTiles(
                                tileRow.tile.aliased_data[childAlias],
                            )
                        "
                        :parent-tile-id="tileRow.tileId"
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
    border-inline-start: 0.4rem solid var(--p-primary-color);
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
    min-inline-size: 0;
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
    min-inline-size: 14rem;
    color: var(--p-text-muted-color);
}

.data-folio-field dd {
    margin: 0;
}
</style>
