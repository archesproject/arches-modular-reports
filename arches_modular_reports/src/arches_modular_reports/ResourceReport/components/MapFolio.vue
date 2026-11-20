<script setup lang="ts">
import { computed, ref } from "vue";
import { useGettext } from "vue3-gettext";

import Badge from "openvue/badge";
import Button from "openvue/button";
import Message from "openvue/message";
import Tag from "openvue/tag";

import BasemapPanel from "@/arches_vue_components/components/MapComponent/components/BasemapPanel/BasemapPanel.vue";
import OverlayPanel from "@/arches_vue_components/components/MapComponent/components/OverlayPanel/OverlayPanel.vue";
import GenericWidget from "@/arches_vue_components/generics/GenericWidget/GenericWidget.vue";
import NodeValue from "@/arches_modular_reports/ResourceReport/components/NodeValue.vue";
import ReportFolio from "@/arches_modular_reports/ResourceReport/components/ReportFolio.vue";

import { useDefaultMapInteractionTools } from "@/arches_vue_components/components/MapComponent/composables/useDefaultMapInteractionTools.ts";
import { VIEW } from "@/arches_vue_components/widgets/constants.ts";
import { useFolio } from "@/arches_modular_reports/ResourceReport/composables/useFolio.ts";
import { childNodegroupAliases } from "@/arches_modular_reports/ResourceReport/utils/graph-nodes.ts";
import { nodeHasData } from "@/arches_modular_reports/ResourceReport/utils/localized-text.ts";
import { aliasedNodeDataOf } from "@/arches_modular_reports/ResourceReport/utils/tiles.ts";

import type { Component } from "vue";

import type {
    MapHeaderAction,
    MapSettings,
} from "@/arches_vue_components/components/MapComponent/types.ts";
import type { AliasedTileData } from "@/arches_vue_components/types.ts";
import type {
    ComponentNode,
    MapFolioConfig,
} from "@/arches_modular_reports/ResourceReport/types.ts";

const REPORT_FOLIO_COMPONENT =
    "arches_modular_reports/ResourceReport/components/ReportFolio";
const EDIT_ACTION = "edit";
const DELETE_ACTION = "delete";
const REPORT_MAP_TOOL_COMPONENTS: Component[] = [BasemapPanel, OverlayPanel];
const REPORT_MAP_SETTINGS: Partial<MapSettings> = {
    scrollZoomRequiresKey: true,
};

const { component } = defineProps<{
    component: ComponentNode<MapFolioConfig>;
}>();

const { $gettext } = useGettext();
const {
    reportData,
    nodegroupAlias,
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
const reportMapTools = useDefaultMapInteractionTools().filter((tool) =>
    REPORT_MAP_TOOL_COMPONENTS.includes(tool.component),
);

const currentTileIndex = ref(0);

const visibleWidgets = computed(() =>
    nodegroupWidgetConfig.value.card_x_node_x_widgets.filter(
        (widget) => widget.visible,
    ),
);

const mapWidget = computed(() =>
    visibleWidgets.value.find(
        (widget) => widget.node.alias === component.config.node_alias,
    ),
);

const currentTile = computed(
    () => tiles.value[Math.min(currentTileIndex.value, tiles.value.length - 1)],
);

const isMapShown = computed(
    () =>
        mapWidget.value !== undefined &&
        hasValue(currentTile.value, mapWidget.value.node.alias),
);

const fieldWidgets = computed(() =>
    visibleWidgets.value.filter(
        (widget) => widget !== mapWidget.value || !isMapShown.value,
    ),
);

const headerActions = computed<MapHeaderAction[]>(() => {
    const tile = currentTile.value;
    const entry = tileLabel(tile);
    const isBusy = reportData.value.changeSet.isBusy.value;
    if (isEditableTile(tile)) {
        return [
            {
                id: DELETE_ACTION,
                label: $gettext("Delete"),
                icon: "pi pi-trash",
                ariaLabel: $gettext("Delete map for %{entry}", { entry }, true),
                disabled: isBusy,
                onClick: () => deleteTile(tile.tileid),
            },
            {
                id: EDIT_ACTION,
                label: $gettext("Edit"),
                icon: "pi pi-pencil",
                ariaLabel: $gettext("Edit map for %{entry}", { entry }, true),
                onClick: () => editTile(tile.tileid),
            },
        ];
    }
    if (isMarkedForDeletion(tile)) {
        return [
            {
                id: DELETE_ACTION,
                label: $gettext("Undo delete"),
                icon: "pi pi-undo",
                ariaLabel: $gettext(
                    "Undo deleting map for %{entry}",
                    { entry },
                    true,
                ),
                disabled: isBusy,
                onClick: () => undoDelete(tile.tileid),
            },
        ];
    }
    return [];
});

const childFolioNodes = computed(() =>
    childNodegroupAliases(
        reportData.value.nodegroupWidgetConfigs,
        nodegroupAlias.value,
    ).map((childAlias) => ({
        component: REPORT_FOLIO_COMPONENT,
        config: { nodegroup_alias: childAlias },
    })),
);

const emptyMessage = computed(() =>
    $gettext("Nothing recorded for %{name}.", { name: cardName.value }, true),
);

function hasValue(tile: AliasedTileData, nodeAlias: string): boolean {
    return nodeHasData(
        nodeAlias,
        aliasedNodeDataOf(tile, nodeAlias),
        reportData.value.nodeTextContext,
    );
}

function showPreviousTile(): void {
    currentTileIndex.value = Math.max(currentTileIndex.value - 1, 0);
}

function showNextTile(): void {
    currentTileIndex.value = Math.min(
        currentTileIndex.value + 1,
        tiles.value.length - 1,
    );
}
</script>

<template>
    <div
        ref="folio"
        class="map-folio"
        :class="{ 'map-folio-flash': isFlashed }"
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
            <div class="map-folio-header">
                <span class="map-folio-name">{{ cardName }}</span>
                <Badge
                    v-if="tiles.length > 1"
                    class="map-folio-count"
                    severity="secondary"
                    :value="tiles.length"
                />
                <Button
                    v-if="isAddable && tiles.length > 0"
                    class="map-folio-add"
                    variant="link"
                    size="small"
                    :label="$gettext('Add')"
                    :disabled="reportData.changeSet.isBusy.value"
                    @click="addTile"
                />
            </div>
            <div
                v-if="tiles.length === 0"
                class="map-folio-empty"
            >
                <span class="map-folio-empty-message">
                    {{ emptyMessage }}
                </span>
                <Button
                    v-if="isAddable"
                    variant="link"
                    size="small"
                    :label="$gettext('Add')"
                    :disabled="reportData.changeSet.isBusy.value"
                    @click="addTile"
                />
            </div>
            <div
                v-else
                class="map-folio-card"
            >
                <GenericWidget
                    v-if="isMapShown && mapWidget !== undefined"
                    :key="currentTile.tileid ?? currentTileIndex"
                    :aliased-node-data="
                        aliasedNodeDataOf(currentTile, mapWidget.node.alias)
                    "
                    :card-x-node-x-widget-data="mapWidget"
                    :graph-slug="reportData.context.graph.slug"
                    :mode="VIEW"
                    :node-alias="mapWidget.node.alias"
                    :should-show-label="false"
                    :interaction-tools="reportMapTools"
                    :header-actions="headerActions"
                    :default-settings="REPORT_MAP_SETTINGS"
                />
                <div
                    class="map-folio-details"
                    :class="{
                        'map-folio-deleted': isPendingDelete(currentTile),
                    }"
                >
                    <div class="map-folio-fields">
                        <div
                            v-for="widget in fieldWidgets"
                            :key="widget.id"
                            class="map-folio-field"
                        >
                            <span class="map-folio-field-label">
                                {{ widget.label }}
                            </span>
                            <div
                                v-if="hasValue(currentTile, widget.node.alias)"
                                class="map-folio-field-value"
                            >
                                <NodeValue
                                    :node-data="
                                        aliasedNodeDataOf(
                                            currentTile,
                                            widget.node.alias,
                                        )!
                                    "
                                    :widget="widget"
                                />
                            </div>
                            <span
                                v-else
                                class="map-folio-empty-message"
                            >
                                {{ $gettext("No value recorded.") }}
                            </span>
                        </div>
                    </div>
                    <div
                        v-if="isEditableTile(currentTile)"
                        class="map-folio-actions"
                    >
                        <Button
                            variant="link"
                            size="small"
                            :label="$gettext('Edit')"
                            :aria-label="
                                $gettext(
                                    'Edit %{entry}',
                                    { entry: tileLabel(currentTile) },
                                    true,
                                )
                            "
                            @click="editTile(currentTile.tileid)"
                        />
                        <Button
                            class="map-folio-delete"
                            variant="link"
                            size="small"
                            :label="$gettext('Delete')"
                            :aria-label="
                                $gettext(
                                    'Delete %{entry}',
                                    { entry: tileLabel(currentTile) },
                                    true,
                                )
                            "
                            :disabled="reportData.changeSet.isBusy.value"
                            @click="deleteTile(currentTile.tileid)"
                        />
                    </div>
                    <div
                        v-else-if="isMarkedForDeletion(currentTile)"
                        class="map-folio-actions"
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
                                    { entry: tileLabel(currentTile) },
                                    true,
                                )
                            "
                            :disabled="reportData.changeSet.isBusy.value"
                            @click="undoDelete(currentTile.tileid)"
                        />
                    </div>
                </div>
                <div
                    v-if="childFolioNodes.length > 0"
                    class="map-folio-children"
                >
                    <ReportFolio
                        v-for="childFolioNode in childFolioNodes"
                        :key="`${childFolioNode.config.nodegroup_alias}-${currentTileIndex}`"
                        :component="childFolioNode"
                        :parent-tile="currentTile"
                    />
                </div>
                <div
                    v-if="tiles.length > 1"
                    class="map-folio-pager"
                >
                    <span class="map-folio-pager-label">
                        {{ $gettext("Additional Data") }}
                    </span>
                    <Button
                        icon="pi pi-chevron-left"
                        variant="outlined"
                        size="small"
                        :aria-label="$gettext('Previous entry')"
                        :disabled="currentTileIndex === 0"
                        @click="showPreviousTile"
                    />
                    <span class="map-folio-pager-position">
                        {{
                            $gettext("%{position} of %{count}", {
                                position: String(currentTileIndex + 1),
                                count: String(tiles.length),
                            })
                        }}
                    </span>
                    <Button
                        icon="pi pi-chevron-right"
                        variant="outlined"
                        size="small"
                        :aria-label="$gettext('Next entry')"
                        :disabled="currentTileIndex === tiles.length - 1"
                        @click="showNextTile"
                    />
                </div>
            </div>
        </template>
    </div>
</template>

<style scoped>
.map-folio {
    --map-header-button-font-size: 1.2rem;
    display: flex;
    flex-direction: column;
    gap: 0.8rem;
    isolation: isolate;
    border-radius: var(--p-content-border-radius);
}

.map-folio:not(:first-child) {
    padding-block-start: 0.8rem;
}

.map-folio-header {
    display: flex;
    align-items: center;
    gap: 0.6rem;
}

.map-folio-name {
    font-size: 1.5rem;
    font-weight: 600;
}

.map-folio-header .map-folio-count {
    min-inline-size: 2rem;
    block-size: 2rem;
    padding-inline: 0.6rem;
    border-radius: 1rem;
    background: var(--resource-report-accent-background);
    color: var(--p-primary-color);
    font-size: 1.2rem;
    font-weight: 700;
    line-height: 2rem;
}

.map-folio-add {
    margin-inline-start: auto;
}

.map-folio-empty {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.8rem;
}

.map-folio-empty-message {
    color: var(--p-text-muted-color);
    font-style: italic;
}

.map-folio-card {
    display: flex;
    flex-direction: column;
    gap: 1.2rem;
}

.map-folio-details {
    display: flex;
    flex-direction: column;
    gap: 1.2rem;
    padding-inline: 1.2rem;
    border-inline-start: 0.3rem solid var(--p-primary-color);
}

.map-folio-deleted .map-folio-fields {
    opacity: 0.6;
    text-decoration: line-through;
}

.map-folio-fields {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
    font-size: 1.3rem;
}

.map-folio-field {
    display: flex;
    flex-direction: row;
    gap: 0.75rem;
}

.map-folio-field-label {
    color: var(--p-text-muted-color);
}

.map-folio-field-value {
    color: var(--p-text-color);
    font-weight: 500;
}

.map-folio-field-value :deep(p) {
    margin-block: 0;
}

.map-folio-actions {
    display: flex;
    align-items: center;
    gap: 0.8rem;
}

.map-folio-delete,
.map-folio-delete:not(:disabled):hover,
.map-folio-delete:not(:disabled):active {
    color: var(--p-button-text-danger-color);
}

.map-folio-children {
    display: flex;
    flex-direction: column;
    gap: 1.2rem;
    padding-block-start: 0.8rem;
    border-block-start: 0.1rem solid var(--p-content-border-color);
}

.map-folio-pager {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1.2rem;
    padding-block: 0.8rem;
    border-block-start: 0.1rem solid var(--p-content-border-color);
}

.map-folio-pager-label {
    color: var(--p-text-muted-color);
    font-size: 1.2rem;
    font-weight: 600;
}

.map-folio-pager-position {
    color: var(--p-text-muted-color);
    font-size: 1.2rem;
}

.map-folio-flash {
    animation: map-folio-flash 1.6s ease-out;
}

@keyframes map-folio-flash {
    from {
        background: var(--p-highlight-background);
        box-shadow: 0 0 0 0.8rem var(--p-highlight-background);
    }
}
</style>
