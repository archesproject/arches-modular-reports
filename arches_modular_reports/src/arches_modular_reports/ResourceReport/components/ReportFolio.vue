<script setup lang="ts">
import { computed, ref } from "vue";
import { useGettext } from "vue3-gettext";

import Badge from "openvue/badge";
import Button from "openvue/button";
import Message from "openvue/message";
import Tag from "openvue/tag";

import GenericWidget from "@/arches_vue_components/generics/GenericWidget/GenericWidget.vue";

import { VIEW } from "@/arches_vue_components/widgets/constants.ts";
import { useFolio } from "@/arches_modular_reports/ResourceReport/composables/useFolio.ts";
import { childNodegroupAliases } from "@/arches_modular_reports/ResourceReport/utils/graph-nodes.ts";
import { aliasedNodeDataOf } from "@/arches_modular_reports/ResourceReport/utils/tiles.ts";

import type { AliasedTileData } from "@/arches_vue_components/types.ts";
import type {
    ComponentNode,
    FolioConfig,
} from "@/arches_modular_reports/ResourceReport/types.ts";

const { component, parentTile = null } = defineProps<{
    component: ComponentNode<FolioConfig>;
    parentTile?: AliasedTileData | null;
}>();

const { $gettext } = useGettext();
const {
    reportData,
    nodegroupAlias,
    hasNodegroup,
    nodegroupWidgetConfig,
    cardName,
    parentTileId,
    isNested,
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
} = useFolio(
    () => component,
    () => parentTile,
);

const isOpen = ref(tiles.value.length > 0);

const visibleWidgets = computed(() =>
    nodegroupWidgetConfig.value.card_x_node_x_widgets.filter(
        (widget) => widget.visible,
    ),
);

const childFolioNodes = computed(() =>
    childNodegroupAliases(
        reportData.value.nodegroupWidgetConfigs,
        nodegroupAlias.value,
    ).map((childAlias) => ({
        component: component.component,
        config: { nodegroup_alias: childAlias },
    })),
);

const isSingleTileCard = computed(
    () => nodegroupWidgetConfig.value.cardinality !== "n",
);

const singleTile = computed(() => {
    if (!isSingleTileCard.value || tiles.value.length === 0) {
        return null;
    }
    return tiles.value[0];
});

const emptyMessage = computed(() => {
    if (parentTileId.value === null) {
        return $gettext(
            "No %{name} have been recorded.",
            { name: cardName.value },
            true,
        );
    }
    return $gettext(
        "No %{name} have been recorded for this entry.",
        { name: cardName.value },
        true,
    );
});

const isHeaderAddVisible = computed(
    () => isAddable.value && (isNested.value || tiles.value.length > 0),
);

const isEmptyAddVisible = computed(() => isAddable.value && !isNested.value);

const isBodyVisible = computed(() => !isNested.value || isOpen.value);

const toggleIcon = computed(() => {
    if (isOpen.value) {
        return "pi pi-chevron-down";
    }
    return "pi pi-chevron-right";
});

const tileClass = computed(() => {
    if (isNested.value) {
        return "report-folio-entry";
    }
    return "report-folio-tile";
});

function hasValue(tile: AliasedTileData, nodeAlias: string): boolean {
    const nodeData = aliasedNodeDataOf(tile, nodeAlias);
    return nodeData !== null && nodeData.display_value !== "";
}

function toggleOpen(): void {
    isOpen.value = !isOpen.value;
}
</script>

<template>
    <div
        ref="folio"
        class="report-folio-anchor"
        :class="{
            'report-folio-flash': isFlashed,
            'report-folio-separated': !isNested,
        }"
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
        <div
            v-else
            class="report-folio"
        >
            <div class="report-folio-header">
                <Button
                    v-if="isNested"
                    class="report-folio-toggle"
                    variant="text"
                    size="small"
                    :aria-expanded="isOpen"
                    @click="toggleOpen"
                >
                    <i
                        aria-hidden="true"
                        :class="toggleIcon"
                    />
                    <span>{{ cardName }}</span>
                </Button>
                <span
                    v-else
                    class="report-folio-name"
                >
                    {{ cardName }}
                </span>
                <Badge
                    v-if="tiles.length > 1"
                    class="report-folio-count"
                    severity="secondary"
                    :value="tiles.length"
                />
                <div
                    class="report-folio-header-actions"
                    :class="{ 'report-folio-header-actions-end': !isNested }"
                >
                    <Button
                        v-if="isHeaderAddVisible"
                        variant="link"
                        size="small"
                        :label="$gettext('Add')"
                        :disabled="reportData.changeSet.isBusy.value"
                        @click="addTile"
                    />
                    <template
                        v-if="singleTile !== null && isEditableTile(singleTile)"
                    >
                        <Button
                            variant="link"
                            size="small"
                            :label="$gettext('Edit')"
                            :aria-label="
                                $gettext(
                                    'Edit %{entry}',
                                    { entry: tileLabel(singleTile) },
                                    true,
                                )
                            "
                            @click="editTile(singleTile.tileid)"
                        />
                        <Button
                            class="report-folio-delete"
                            variant="link"
                            size="small"
                            :label="$gettext('Delete')"
                            :aria-label="
                                $gettext(
                                    'Delete %{entry}',
                                    { entry: tileLabel(singleTile) },
                                    true,
                                )
                            "
                            :disabled="reportData.changeSet.isBusy.value"
                            @click="deleteTile(singleTile.tileid)"
                        />
                    </template>
                    <template
                        v-else-if="
                            singleTile !== null &&
                            isMarkedForDeletion(singleTile)
                        "
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
                                    { entry: tileLabel(singleTile) },
                                    true,
                                )
                            "
                            :disabled="reportData.changeSet.isBusy.value"
                            @click="undoDelete(singleTile.tileid)"
                        />
                    </template>
                </div>
            </div>
            <div
                v-if="isBodyVisible"
                class="report-folio-body"
                :class="{ 'report-folio-body-nested': isNested }"
            >
                <div
                    v-if="tiles.length === 0"
                    class="report-folio-empty"
                >
                    <span class="report-folio-empty-message">
                        {{ emptyMessage }}
                    </span>
                    <Button
                        v-if="isEmptyAddVisible"
                        variant="link"
                        size="small"
                        :label="$gettext('Add')"
                        :disabled="reportData.changeSet.isBusy.value"
                        @click="addTile"
                    />
                </div>
                <div
                    v-for="(tile, tileIndex) in tiles"
                    :key="tile.tileid ?? tileIndex"
                    :class="[
                        tileClass,
                        { 'report-folio-tile-deleted': isPendingDelete(tile) },
                    ]"
                >
                    <div class="report-folio-fields">
                        <template
                            v-for="widget in visibleWidgets"
                            :key="widget.id"
                        >
                            <GenericWidget
                                v-if="hasValue(tile, widget.node.alias)"
                                :aliased-node-data="
                                    aliasedNodeDataOf(tile, widget.node.alias)
                                "
                                :card-x-node-x-widget-data="widget"
                                :graph-slug="reportData.context.graph.slug"
                                :mode="VIEW"
                                :node-alias="widget.node.alias"
                            />
                            <div
                                v-else
                                class="report-folio-empty-field"
                            >
                                <span class="report-folio-empty-field-label">
                                    {{ widget.label }}
                                </span>
                                <span class="report-folio-empty-message">
                                    {{ $gettext("No value recorded.") }}
                                </span>
                            </div>
                        </template>
                    </div>
                    <div
                        v-if="!isSingleTileCard && isEditableTile(tile)"
                        class="report-folio-tile-actions"
                    >
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
                            @click="editTile(tile.tileid)"
                        />
                        <Button
                            class="report-folio-delete"
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
                    </div>
                    <div
                        v-else-if="
                            !isSingleTileCard && isMarkedForDeletion(tile)
                        "
                        class="report-folio-tile-actions"
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
                    </div>
                    <div
                        v-if="childFolioNodes.length > 0"
                        class="report-folio-children"
                    >
                        <ReportFolio
                            v-for="childFolioNode in childFolioNodes"
                            :key="childFolioNode.config.nodegroup_alias"
                            :component="childFolioNode"
                            :parent-tile="tile"
                        />
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
.report-folio-anchor {
    isolation: isolate;
    border-radius: var(--p-content-border-radius);
}

.report-folio-separated:not(:first-child) {
    padding-block-start: 0.8rem;
}

.report-folio-flash {
    animation: report-folio-flash 1.6s ease-out;
}

@keyframes report-folio-flash {
    from {
        background: var(--p-highlight-background);
        box-shadow: 0 0 0 0.8rem var(--p-highlight-background);
    }
}

.report-folio {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
}

.report-folio-header {
    display: flex;
    align-items: center;
    gap: 0.6rem;
}

.report-folio-name {
    font-size: 1.5rem;
    font-weight: 600;
}

.report-folio-toggle {
    gap: 0.6rem;
    padding-inline: 0;
    color: var(--p-text-muted-color);
    font-size: 1.2rem;
    font-weight: 700;
    text-transform: uppercase;
}

.report-folio-count {
    min-inline-size: 2rem;
    block-size: 2rem;
    font-size: 1.2rem;
    line-height: 2rem;
}

.report-folio-header-actions {
    display: flex;
    align-items: center;
    gap: 0.4rem;
}

.report-folio-header-actions-end {
    margin-inline-start: auto;
}

.report-folio-body {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
}

.report-folio-body-nested {
    padding-inline-start: 1.8rem;
}

.report-folio-empty {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.8rem;
}

.report-folio-empty-message {
    color: var(--p-text-muted-color);
    font-style: italic;
}

.report-folio-tile,
.report-folio-entry {
    display: flex;
    flex-direction: column;
}

.report-folio-entry {
    gap: 1.2rem;
}

.report-folio-tile {
    padding-inline: 1.2rem;
    border-inline-start: 0.3rem solid var(--p-primary-color);
}

.report-folio-entry + .report-folio-entry {
    padding-block-start: 1.2rem;
    border-block-start: 0.1rem solid var(--p-content-border-color);
}

.report-folio-fields {
    display: flex;
    flex-direction: column;
}

.report-folio-fields > .widget {
    flex-direction: row;
    align-items: center;
    gap: 5px;
    font-weight: 600;
}

.report-folio-fields :deep(.widget-label) {
    font-weight: 400;
}

.report-folio-tile-deleted > .report-folio-fields {
    opacity: 0.6;
    text-decoration: line-through;
}

.report-folio-empty-field {
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: 5px;
}

.report-folio-empty-field-label {
    font-weight: 400;
}

.report-folio-tile-actions {
    display: flex;
    align-items: center;
    gap: 0.8rem;
}

.report-folio-tile-actions > .p-button {
    padding-inline: 0.2rem;
}

.report-folio-delete,
.report-folio-delete:not(:disabled):hover,
.report-folio-delete:not(:disabled):active {
    color: var(--p-button-text-danger-color);
}

.report-folio-children {
    display: flex;
    flex-direction: column;
    gap: 1.2rem;
    padding-block-start: 0.8rem;
    border-block-start: 0.1rem solid var(--p-content-border-color);
}
</style>
