<script setup lang="ts">
import { computed, ref } from "vue";
import { useGettext } from "vue3-gettext";

import Badge from "openvue/badge";
import Button from "openvue/button";
import Message from "openvue/message";
import Tag from "openvue/tag";

import GenericWidget from "@/arches_vue_components/generics/GenericWidget/GenericWidget.vue";
import ReportFolio from "@/arches_modular_reports/ResourceReport/components/ReportFolio.vue";

import { VIEW } from "@/arches_vue_components/widgets/constants.ts";
import { useFolio } from "@/arches_modular_reports/ResourceReport/composables/useFolio.ts";
import { childNodegroupAliases } from "@/arches_modular_reports/ResourceReport/utils/graph-nodes.ts";
import { aliasedNodeDataOf } from "@/arches_modular_reports/ResourceReport/utils/tiles.ts";

import type { AliasedTileData } from "@/arches_vue_components/types.ts";
import type {
    ComponentNode,
    MapFolioConfig,
} from "@/arches_modular_reports/ResourceReport/types.ts";

const REPORT_FOLIO_COMPONENT =
    "arches_modular_reports/ResourceReport/components/ReportFolio";

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
    $gettext("No %{name} have been recorded.", { name: cardName.value }, true),
);

function hasValue(tile: AliasedTileData, nodeAlias: string): boolean {
    const nodeData = aliasedNodeDataOf(tile, nodeAlias);
    return nodeData !== null && nodeData.display_value !== "";
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
                />
                <div
                    class="map-folio-details"
                    :class="{
                        'map-folio-deleted': isPendingDelete(currentTile),
                    }"
                >
                    <div class="map-folio-fields">
                        <template
                            v-for="widget in fieldWidgets"
                            :key="widget.id"
                        >
                            <GenericWidget
                                v-if="hasValue(currentTile, widget.node.alias)"
                                :aliased-node-data="
                                    aliasedNodeDataOf(
                                        currentTile,
                                        widget.node.alias,
                                    )
                                "
                                :card-x-node-x-widget-data="widget"
                                :graph-slug="reportData.context.graph.slug"
                                :mode="VIEW"
                                :node-alias="widget.node.alias"
                            />
                            <div
                                v-else
                                class="map-folio-empty-field"
                            >
                                <span class="map-folio-empty-field-label">
                                    {{ widget.label }}
                                </span>
                                <span class="map-folio-empty-message">
                                    {{ $gettext("No value recorded.") }}
                                </span>
                            </div>
                        </template>
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
    gap: 1.4rem;
}

.map-folio-empty-field {
    display: flex;
    flex-direction: column;
}

.map-folio-fields > .widget {
    font-weight: 600;
}

.map-folio-fields :deep(.widget-label) {
    font-weight: 400;
}

.map-folio-empty-field-label {
    font-weight: 400;
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
