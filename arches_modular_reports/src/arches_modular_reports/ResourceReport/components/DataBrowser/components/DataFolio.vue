<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";
import Tag from "openvue/tag";

import DataFolioTileActions from "@/arches_modular_reports/ResourceReport/components/DataBrowser/components/DataFolioTileActions.vue";
import HighlightedText from "@/arches_modular_reports/ResourceReport/components/DataBrowser/components/HighlightedText.vue";

import {
    folioMatches,
    nodegroupMatches,
    ownLabelsMatch,
} from "@/arches_modular_reports/ResourceReport/utils/data-filter.ts";
import { datatypeIcon } from "@/arches_modular_reports/ResourceReport/utils/datatype-icon.ts";
import {
    childNodegroupAliases,
    nodegroupLineage,
} from "@/arches_modular_reports/ResourceReport/utils/graph-nodes.ts";
import {
    aliasedNodeDataOf,
    canAddTile,
    containsTile,
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
    TileChangeType,
} from "@/arches_modular_reports/ResourceReport/types.ts";

const EDIT_TILE = "edit-tile" as const;
const EMPTY_VALUE = "—";

const {
    nodegroupAlias,
    nodegroupWidgetConfigs,
    tiles,
    parentTileId,
    changeSet,
    query,
    matchedByAncestor,
    selectedTileId,
    isEditable,
} = defineProps<{
    nodegroupAlias: string;
    nodegroupWidgetConfigs: Record<string, NodegroupWidgetConfig>;
    tiles: AliasedTileData[];
    parentTileId: string | null;
    changeSet: ResourceChangeSet;
    query: string;
    matchedByAncestor: boolean;
    selectedTileId: string | null;
    isEditable: boolean;
}>();

const emit = defineEmits<{
    (event: typeof EDIT_TILE, editTileRequest: EditTileRequest): void;
}>();

const { $gettext } = useGettext();

const isFolioToggledOpen = ref<boolean | null>(null);
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

const nestingDepth = computed(
    () => nodegroupLineage(nodegroupWidgetConfigs, nodegroupAlias).length - 1,
);

const childAliases = computed(() =>
    childNodegroupAliases(nodegroupWidgetConfigs, nodegroupAlias),
);

const isAddable = computed(
    () =>
        isEditable &&
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

const isFiltering = computed(() => query !== "");

const isSingle = computed(
    () => nodegroupWidgetConfig.value.cardinality !== "n",
);

const isTopLevel = computed(
    () => nodegroupWidgetConfig.value.parent_nodegroup_alias === null,
);

const isFolioExpanded = computed(
    () => !isTopLevel.value || (isFolioToggledOpen.value ?? isFiltering.value),
);

const isReorderable = computed(() => !isFiltering.value && tiles.length > 1);

const childrenMatchedByAncestor = computed(
    () =>
        matchedByAncestor ||
        (isFiltering.value &&
            ownLabelsMatch(nodegroupWidgetConfig.value, query)),
);

const tileRows = computed(() =>
    tiles
        .map((tile, tileIndex) => {
            const tileId = tile.tileid ?? "";
            const changeType = changeSet.changeTypeForTile(tileId);
            const isMarkedForDeletion = changeType === "delete";
            const isPendingDelete = changeSet.isPendingDelete(tileId);
            const isSelected = selectedTileId === tileId;
            return {
                tile,
                tileId,
                tileIndex,
                label: tileLabel(tile),
                changeTag: changeTag(changeType),
                isMarkedForDeletion,
                isPendingDelete,
                stateClasses: {
                    "data-folio-tile-pending":
                        changeType !== null && !isPendingDelete,
                    "data-folio-tile-deleted": isPendingDelete,
                    "data-folio-tile-selected": isSelected,
                    "data-folio-tile-selected-added":
                        isSelected && changeType === "add",
                },
                isLocked:
                    !isEditable ||
                    !nodegroupWidgetConfig.value.is_writable ||
                    (isPendingDelete && !isMarkedForDeletion),
                isExpanded: isSingle.value || isExpanded(tileId),
                childFolios: visibleChildFolios(tile),
            };
        })
        .filter((tileRow) => isTileVisible(tileRow.tile)),
);

const singleTileRow = computed(() =>
    isSingle.value ? tileRows.value[0] ?? null : null,
);

const placeholderChildFolios = computed(() => visibleChildFolios(null));

const hasPendingChange = computed(() => {
    if (isTopLevel.value) {
        return changeSet.pendingChanges.value.some((change) =>
            nodegroupLineage(
                nodegroupWidgetConfigs,
                change.nodegroupAlias,
            ).includes(nodegroupAlias),
        );
    }
    return (
        tileRows.value.some((tileRow) => tileRow.changeTag !== null) ||
        changeSet.pendingChanges.value.some(
            (change) =>
                change.type === "reorder" &&
                change.nodegroupAlias === nodegroupAlias &&
                change.parentTileId === parentTileId,
        )
    );
});

const isHeaderPending = computed(() => {
    if (isTopLevel.value) {
        return hasPendingChange.value && !isFolioExpanded.value;
    }
    return hasPendingChange.value && !isSingle.value;
});

const isCountShown = computed(
    () => tiles.length > 0 && (isTopLevel.value || !isSingle.value),
);

const selectedBranchTileId = computed(() => {
    if (selectedTileId === null) {
        return null;
    }
    const branchTile = tiles.find((tile) => containsTile(tile, selectedTileId));
    return branchTile?.tileid ?? null;
});

watch(
    () => query,
    () => {
        if (isFolioToggledOpen.value === false) {
            isFolioToggledOpen.value = null;
        }
        collapsedTileIds.value = new Set();
    },
);

watch(
    selectedBranchTileId,
    (branchTileId) => {
        if (branchTileId === null) {
            return;
        }
        isFolioToggledOpen.value = true;
        collapsedTileIds.value.delete(branchTileId);
        expandedTileIds.value.add(branchTileId);
    },
    { immediate: true },
);

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
    changeType: TileChangeType | null,
): { label: string; severity: "success" | "info" | "danger" } | null {
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

function isTileVisible(tile: AliasedTileData): boolean {
    if (!isFiltering.value || childrenMatchedByAncestor.value) {
        return true;
    }
    return (
        tileSearchText(tile).includes(query) ||
        childAliases.value.some((childAlias) =>
            nodegroupMatches(nodegroupWidgetConfigs, childAlias, query),
        )
    );
}

function visibleChildFolios(
    tile: AliasedTileData | null,
): { nodegroupAlias: string; tiles: AliasedTileData[] }[] {
    return childAliases.value
        .map((childAlias) => ({
            nodegroupAlias: childAlias,
            tiles: nodegroupTiles(tile?.aliased_data[childAlias]),
        }))
        .filter(
            (childFolio) =>
                !isFiltering.value ||
                childrenMatchedByAncestor.value ||
                folioMatches(
                    nodegroupWidgetConfigs,
                    childFolio.nodegroupAlias,
                    childFolio.tiles,
                    query,
                ),
        );
}

function isExpanded(tileId: string): boolean {
    if (collapsedTileIds.value.has(tileId)) {
        return false;
    }
    if (expandedTileIds.value.has(tileId)) {
        return true;
    }
    return isFiltering.value;
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

function toggleFolio(): void {
    isFolioToggledOpen.value = !isFolioExpanded.value;
}

function onHeaderClick(): void {
    if (isTopLevel.value) {
        toggleFolio();
    }
}

async function addTile(): Promise<void> {
    const newTileId = await changeSet.addTile(nodegroupAlias, parentTileId);
    if (newTileId !== null) {
        isFolioToggledOpen.value = true;
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
    const orderedTileIds = tiles.map((tile) => tile.tileid ?? "");
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
        <header
            class="data-folio-header"
            :class="{
                'data-folio-header-top': isTopLevel,
                'data-folio-header-nested': !isTopLevel,
                'data-folio-header-open': isTopLevel && isFolioExpanded,
                'data-folio-header-pending': isHeaderPending,
            }"
            @click="onHeaderClick"
        >
            <span class="data-folio-indent">
                <span
                    v-for="level in nestingDepth"
                    :key="level"
                    class="data-folio-indent-step"
                />
            </span>
            <Button
                v-if="isTopLevel"
                class="data-folio-toggle"
                variant="text"
                size="small"
                :icon="expandIcon(isFolioExpanded)"
                :aria-expanded="isFolioExpanded"
                :aria-label="
                    $gettext(
                        'Show entries for %{card}',
                        {
                            card: cardName,
                        },
                        true,
                    )
                "
                @click.stop="toggleFolio"
            />
            <i
                v-else
                class="pi pi-table data-folio-icon"
                aria-hidden="true"
            />
            <span class="data-folio-name">
                <HighlightedText
                    :text="cardName"
                    :query="query"
                />
            </span>
            <span
                v-if="isCountShown"
                class="data-folio-count"
            >
                {{ tiles.length }}
            </span>
            <div
                class="data-folio-actions"
                @click.stop
            >
                <template v-if="singleTileRow">
                    <Tag
                        v-if="singleTileRow.changeTag"
                        :value="singleTileRow.changeTag.label"
                        :severity="singleTileRow.changeTag.severity"
                    />
                    <DataFolioTileActions
                        v-if="!singleTileRow.isLocked"
                        :label="singleTileRow.label"
                        :is-marked-for-deletion="
                            singleTileRow.isMarkedForDeletion
                        "
                        :is-busy="changeSet.isBusy.value"
                        @edit="editTile(singleTileRow.tileId)"
                        @delete="deleteTile(singleTileRow.tileId)"
                        @undo-delete="undoDelete(singleTileRow.tileId)"
                    />
                </template>
                <Button
                    v-if="isAddable"
                    class="data-folio-action"
                    variant="outlined"
                    size="small"
                    :label="$gettext('Add')"
                    :aria-label="
                        $gettext(
                            'Add to %{card}',
                            {
                                card: cardName,
                            },
                            true,
                        )
                    "
                    :disabled="changeSet.isBusy.value"
                    @click="addTile"
                />
            </div>
            <span
                class="data-folio-cardinality"
                :class="{ 'data-folio-cardinality-many': !isSingle }"
            >
                {{ cardinalityLabel }}
            </span>
        </header>
        <ul
            v-if="isFolioExpanded && tiles.length > 0"
            class="data-folio-tiles"
        >
            <li
                v-for="tileRow in tileRows"
                :key="tileRow.tileId"
                class="data-folio-tile"
                @dragover="onDragOver"
                @drop="onDrop($event, tileRow.tileIndex)"
            >
                <div
                    v-if="!isSingle"
                    class="data-folio-tile-row"
                    :class="tileRow.stateClasses"
                    :draggable="
                        !tileRow.isLocked &&
                        isReorderable &&
                        !changeSet.isBusy.value
                    "
                    @click="toggleTile(tileRow.tileId, tileRow.isExpanded)"
                    @dragstart="onDragStart($event, tileRow.tileId)"
                    @dragend="onDragEnd"
                >
                    <span class="data-folio-indent">
                        <span
                            v-for="level in nestingDepth"
                            :key="level"
                            class="data-folio-indent-step"
                        />
                    </span>
                    <i
                        v-if="!tileRow.isLocked && isReorderable"
                        class="pi pi-bars data-folio-drag-handle"
                        aria-hidden="true"
                    />
                    <Button
                        class="data-folio-toggle"
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
                        @click.stop="
                            toggleTile(tileRow.tileId, tileRow.isExpanded)
                        "
                    />
                    <span class="data-folio-tile-number">
                        #{{ tileRow.tileIndex + 1 }}
                    </span>
                    <span class="data-folio-summary">
                        <HighlightedText
                            :text="tileRow.label"
                            :query="query"
                        />
                    </span>
                    <div
                        class="data-folio-actions"
                        @click.stop
                    >
                        <Tag
                            v-if="tileRow.changeTag"
                            :value="tileRow.changeTag.label"
                            :severity="tileRow.changeTag.severity"
                        />
                        <template v-if="!tileRow.isLocked && isReorderable">
                            <Button
                                class="data-folio-move"
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
                                class="data-folio-move"
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
                        </template>
                        <DataFolioTileActions
                            v-if="!tileRow.isLocked"
                            :label="tileRow.label"
                            :is-marked-for-deletion="
                                tileRow.isMarkedForDeletion
                            "
                            :is-busy="changeSet.isBusy.value"
                            @edit="editTile(tileRow.tileId)"
                            @delete="deleteTile(tileRow.tileId)"
                            @undo-delete="undoDelete(tileRow.tileId)"
                        />
                    </div>
                </div>
                <div
                    v-if="tileRow.isExpanded"
                    class="data-folio-tile-body"
                >
                    <dl
                        class="data-folio-fields"
                        :class="tileRow.stateClasses"
                    >
                        <div
                            v-for="widget in visibleWidgets"
                            :key="widget.node.alias"
                            class="data-folio-field"
                        >
                            <dt>
                                <span class="data-folio-indent">
                                    <span
                                        v-for="level in nestingDepth"
                                        :key="level"
                                        class="data-folio-indent-step"
                                    />
                                </span>
                                <i
                                    :class="[
                                        datatypeIcon(widget.node.datatype),
                                        'data-folio-field-icon',
                                    ]"
                                    aria-hidden="true"
                                />
                                <HighlightedText
                                    :text="widget.label"
                                    :query="query"
                                />
                            </dt>
                            <dd
                                v-if="
                                    displayValue(
                                        tileRow.tile,
                                        widget.node.alias,
                                    ) === ''
                                "
                                class="data-folio-field-empty"
                            >
                                {{ EMPTY_VALUE }}
                            </dd>
                            <dd v-else>
                                <HighlightedText
                                    :text="
                                        displayValue(
                                            tileRow.tile,
                                            widget.node.alias,
                                        )
                                    "
                                    :query="query"
                                />
                            </dd>
                        </div>
                    </dl>
                    <div
                        v-if="tileRow.childFolios.length > 0"
                        class="data-folio-children"
                    >
                        <DataFolio
                            v-for="childFolio in tileRow.childFolios"
                            :key="childFolio.nodegroupAlias"
                            :nodegroup-alias="childFolio.nodegroupAlias"
                            :nodegroup-widget-configs="nodegroupWidgetConfigs"
                            :tiles="childFolio.tiles"
                            :parent-tile-id="tileRow.tileId"
                            :change-set="changeSet"
                            :query="query"
                            :matched-by-ancestor="childrenMatchedByAncestor"
                            :selected-tile-id="selectedTileId"
                            :is-editable="isEditable"
                            @edit-tile="emit(EDIT_TILE, $event)"
                        />
                    </div>
                </div>
            </li>
        </ul>
        <div
            v-if="isFolioExpanded && tiles.length === 0"
            class="data-folio-tile-body data-folio-placeholder"
            :class="{ 'data-folio-placeholder-top': isTopLevel }"
        >
            <dl class="data-folio-fields">
                <div
                    v-for="widget in visibleWidgets"
                    :key="widget.node.alias"
                    class="data-folio-field"
                >
                    <dt>
                        <span class="data-folio-indent">
                            <span
                                v-for="level in nestingDepth"
                                :key="level"
                                class="data-folio-indent-step"
                            />
                        </span>
                        <i
                            :class="[
                                datatypeIcon(widget.node.datatype),
                                'data-folio-field-icon',
                            ]"
                            aria-hidden="true"
                        />
                        <HighlightedText
                            :text="widget.label"
                            :query="query"
                        />
                    </dt>
                    <dd class="data-folio-field-empty">{{ EMPTY_VALUE }}</dd>
                </div>
            </dl>
            <div
                v-if="placeholderChildFolios.length > 0"
                class="data-folio-children"
            >
                <DataFolio
                    v-for="childFolio in placeholderChildFolios"
                    :key="childFolio.nodegroupAlias"
                    :nodegroup-alias="childFolio.nodegroupAlias"
                    :nodegroup-widget-configs="nodegroupWidgetConfigs"
                    :tiles="childFolio.tiles"
                    :parent-tile-id="null"
                    :change-set="changeSet"
                    :query="query"
                    :matched-by-ancestor="childrenMatchedByAncestor"
                    :selected-tile-id="selectedTileId"
                    :is-editable="false"
                    @edit-tile="emit(EDIT_TILE, $event)"
                />
            </div>
        </div>
    </section>
</template>

<style scoped>
.data-folio {
    display: flex;
    flex-direction: column;
}

.data-folio-indent {
    display: flex;
    flex-shrink: 0;
}

.data-folio-indent-step {
    inline-size: 1.2rem;
}

.data-folio-header {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    min-block-size: 3.7rem;
    padding-block: 0.4rem;
    padding-inline: 0.2rem 0.8rem;
    border-block-end: 0.1rem solid var(--p-content-border-color);
    color: var(--p-text-color);
}

.data-folio-header-top {
    cursor: pointer;
    font-size: 1.3rem;
    font-weight: 700;
    user-select: none;
}

.data-folio-header-nested {
    min-block-size: 3.3rem;
    padding-inline-start: 1.4rem;
    background: var(--resource-report-row-nested-background);
    font-size: 1.15rem;
    font-weight: 600;
}

.data-folio-header-open {
    background: var(--resource-report-row-open-background);
}

.data-folio-header.data-folio-header-pending,
.data-folio-tile-row.data-folio-tile-pending,
.data-folio-fields.data-folio-tile-pending .data-folio-field {
    background: var(--resource-report-pending-background);
    color: var(--resource-report-pending-color);
}

.data-folio-header-pending .data-folio-toggle,
.data-folio-header-pending .data-folio-icon,
.data-folio-tile-pending .data-folio-toggle,
.data-folio-tile-pending .data-folio-drag-handle,
.data-folio-tile-pending .data-folio-tile-number,
.data-folio-tile-pending .data-folio-move,
.data-folio-tile-pending .data-folio-field dt,
.data-folio-tile-pending .data-folio-field dd,
.data-folio-tile-pending .data-folio-field-icon {
    color: var(--resource-report-pending-color);
}

.data-folio-header .data-folio-toggle,
.data-folio-tile-row .data-folio-toggle {
    --p-button-sm-font-size: 0.9rem;
    flex-shrink: 0;
    inline-size: 1.4rem;
    block-size: 2.4rem;
    padding: 0;
    color: var(--p-text-muted-color);
}

.data-folio-tile-row .data-folio-toggle {
    --p-button-sm-font-size: 1rem;
    inline-size: 1.5rem;
    color: var(--p-text-color);
}

.data-folio-icon {
    flex-shrink: 0;
    color: var(--p-text-muted-color);
    font-size: 1.2rem;
}

.data-folio-name {
    flex: 1;
    min-inline-size: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.data-folio-count {
    flex-shrink: 0;
    padding-block: 0.1rem;
    padding-inline: 0.8rem;
    border-radius: 0.8rem;
    background: var(--resource-report-accent-background);
    color: var(--resource-report-accent-color);
    font-size: 1.2rem;
    font-weight: 500;
}

.data-folio-actions {
    display: flex;
    flex-shrink: 0;
    align-items: center;
    gap: 0.3rem;
    cursor: default;
}

.data-folio-actions .data-folio-action {
    --p-button-label-font-weight: 600;
    min-block-size: 2.4rem;
    padding-block: 0.1rem;
    padding-inline: 0.6rem;
    border-color: var(--resource-report-accent-color);
    border-radius: 0.3rem;
    background: var(--resource-report-accent-background);
    color: var(--resource-report-accent-color);
    font-size: 1.1rem;
}

.data-folio-actions .data-folio-action:not(:disabled):hover {
    border-color: var(--resource-report-accent-color);
    background: var(--resource-report-accent-color);
    color: var(--p-primary-contrast-color);
}

.data-folio-actions .data-folio-move {
    inline-size: 2.4rem;
    block-size: 2.4rem;
    padding: 0;
    color: var(--p-text-muted-color);
}

.data-folio-cardinality {
    flex-shrink: 0;
    padding-block: 0.1rem;
    padding-inline: 0.4rem;
    border: 0.1rem solid var(--p-content-border-color);
    border-radius: 0.3rem;
    color: var(--p-text-muted-color);
    font-family: monospace;
    font-size: 1.1rem;
    font-weight: 700;
    letter-spacing: 0.05rem;
    opacity: 0.6;
}

.data-folio-cardinality-many {
    border-color: var(--resource-report-accent-color);
    background: var(--resource-report-accent-background);
    color: var(--resource-report-accent-color);
    opacity: 1;
}

.data-folio-tiles {
    display: flex;
    flex-direction: column;
    margin: 0;
    padding: 0;
    list-style: none;
}

.data-folio-tile-row {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    min-block-size: 3.1rem;
    padding-block: 0.4rem;
    padding-inline: 1.2rem 0.8rem;
    border-block-end: 0.1rem solid var(--p-content-border-color);
    border-inline-start: 0.3rem solid transparent;
    background: var(--resource-report-row-entry-background);
    cursor: pointer;
    font-size: 1.1rem;
    user-select: none;
}

.data-folio-tile-row:hover {
    background: var(--resource-report-row-hover-background);
}

.data-folio-drag-handle {
    flex-shrink: 0;
    color: var(--p-text-color);
    cursor: grab;
    font-size: 1.2rem;
}

.data-folio-tile-number {
    flex-shrink: 0;
    color: var(--p-primary-color);
    font-size: 1.2rem;
    font-weight: 700;
}

.data-folio-summary {
    flex: 1;
    min-inline-size: 0;
    overflow: hidden;
    color: var(--p-text-color);
    font-size: 1.2rem;
    font-weight: 500;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.data-folio-tile-body {
    display: flex;
    flex-direction: column;
}

.data-folio-fields {
    display: flex;
    flex-direction: column;
    margin: 0;
}

.data-folio-field {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding-block: 0.4rem;
    padding-inline: 2rem 0.8rem;
    border-block-end: 0.1rem solid var(--p-content-border-color);
    border-inline-start: 0.3rem solid transparent;
    font-size: 1.2rem;
}

.data-folio-field dt {
    display: flex;
    flex: 1;
    align-items: center;
    gap: 0.6rem;
    min-inline-size: 0;
    overflow: hidden;
    color: var(--p-text-muted-color);
    font-weight: normal;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.data-folio-field-icon {
    flex-shrink: 0;
    font-size: 1.2rem;
}

.data-folio-field dd {
    flex-shrink: 0;
    max-inline-size: 55%;
    margin: 0;
    overflow: hidden;
    color: var(--p-text-color);
    font-weight: 500;
    text-align: end;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.data-folio-field .data-folio-field-empty {
    color: var(--p-text-muted-color);
    font-size: 1.1rem;
    font-style: italic;
    font-weight: normal;
    opacity: 0.55;
}

.data-folio-tile-row.data-folio-tile-deleted,
.data-folio-fields.data-folio-tile-deleted .data-folio-field {
    background: var(--resource-report-deleted-background);
}

.data-folio-tile-deleted .data-folio-summary,
.data-folio-tile-deleted .data-folio-field dt,
.data-folio-tile-deleted .data-folio-field dd {
    opacity: 0.65;
    text-decoration: line-through;
}

.data-folio-tile-deleted .data-folio-tile-number {
    color: var(--resource-report-deleted-color);
}

.data-folio-tile-row.data-folio-tile-selected,
.data-folio-fields.data-folio-tile-selected .data-folio-field {
    border-inline-start-color: var(--resource-report-edited-color);
}

.data-folio-tile-row.data-folio-tile-selected:not(.data-folio-tile-pending):not(
        .data-folio-tile-deleted
    ),
.data-folio-fields.data-folio-tile-selected:not(.data-folio-tile-pending):not(
        .data-folio-tile-deleted
    )
    .data-folio-field {
    background: var(--resource-report-edited-background);
}

.data-folio-tile-row.data-folio-tile-selected-added,
.data-folio-fields.data-folio-tile-selected-added .data-folio-field {
    border-inline-start-color: var(--resource-report-accent-color);
}

.data-folio-tile-row.data-folio-tile-selected.data-folio-tile-deleted,
.data-folio-fields.data-folio-tile-selected.data-folio-tile-deleted
    .data-folio-field {
    border-inline-start-color: var(--resource-report-deleted-color);
}

.data-folio-children {
    display: flex;
    flex-direction: column;
}

.data-folio-placeholder-top > .data-folio-fields > .data-folio-field {
    padding-inline-start: 1.2rem;
}
</style>
