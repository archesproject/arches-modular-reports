<script setup lang="ts">
import { computed } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";

import GenericWidget from "@/arches_vue_components/generics/GenericWidget/GenericWidget.vue";

import { VIEW } from "@/arches_vue_components/widgets/constants.ts";
import { childNodegroupAliases } from "@/arches_modular_reports/ResourceReport/utils/graph-nodes.ts";
import {
    aliasedNodeDataOf,
    canAddTile,
    nodegroupTiles,
} from "@/arches_modular_reports/ResourceReport/utils/tiles.ts";

import type { AliasedTileData } from "@/arches_vue_components/types.ts";
import type { ReportData } from "@/arches_modular_reports/ResourceReport/types.ts";

const { nodegroupAlias, tiles, parentTileId, reportData } = defineProps<{
    nodegroupAlias: string;
    tiles: AliasedTileData[];
    parentTileId: string | null;
    reportData: ReportData;
}>();

const { $gettext } = useGettext();

const nodegroupWidgetConfig = computed(
    () => reportData.nodegroupWidgetConfigs[nodegroupAlias],
);

const cardName = computed(() => nodegroupWidgetConfig.value.card?.name ?? "");

const visibleWidgets = computed(() =>
    nodegroupWidgetConfig.value.card_x_node_x_widgets.filter(
        (widget) => widget.visible,
    ),
);

const childAliases = computed(() =>
    childNodegroupAliases(reportData.nodegroupWidgetConfigs, nodegroupAlias),
);

const emptyMessage = computed(() => {
    const name = cardName.value.toLocaleLowerCase();
    if (parentTileId === null) {
        return $gettext("No %{name} have been recorded.", { name }, true);
    }
    return $gettext(
        "No %{name} have been recorded for this entry.",
        { name },
        true,
    );
});

const isAddable = computed(
    () =>
        reportData.canEdit &&
        canAddTile(
            nodegroupWidgetConfig.value,
            tiles.length,
            parentTileId,
            reportData.changeSet,
        ),
);

function isEditableTile(
    tile: AliasedTileData,
): tile is AliasedTileData & { tileid: string } {
    return (
        reportData.canEdit &&
        nodegroupWidgetConfig.value.is_writable &&
        tile.tileid !== null &&
        !reportData.changeSet.isPendingDelete(tile.tileid)
    );
}

function hasValue(tile: AliasedTileData, nodeAlias: string): boolean {
    return aliasedNodeDataOf(tile, nodeAlias)?.display_value !== "";
}

async function addTile(): Promise<void> {
    const tileId = await reportData.changeSet.addTile(
        nodegroupAlias,
        parentTileId,
    );
    if (tileId !== null) {
        reportData.editor.open({ nodegroupAlias, tileId });
    }
}

function editNode(tileId: string, nodeAlias: string): void {
    reportData.editor.open({ nodegroupAlias, tileId, nodeAlias });
}

function clearNode(tileId: string, nodeAlias: string): void {
    reportData.changeSet.editTile(nodegroupAlias, tileId, {
        [nodeAlias]: { display_value: "", node_value: null, details: [] },
    });
}
</script>

<template>
    <div class="report-folio">
        <div class="report-folio-header">
            <span class="report-folio-name">{{ cardName }}</span>
            <Button
                v-if="isAddable"
                variant="link"
                size="small"
                :label="$gettext('Add')"
                :disabled="reportData.changeSet.isBusy.value"
                @click="addTile"
            />
        </div>
        <span
            v-if="tiles.length === 0"
            class="report-folio-empty"
        >
            {{ emptyMessage }}
        </span>
        <div
            v-for="(tile, tileIndex) in tiles"
            :key="tile.tileid ?? tileIndex"
            class="report-folio-tile"
        >
            <div class="report-folio-fields">
                <div
                    v-for="widget in visibleWidgets"
                    :key="widget.id"
                    class="report-folio-field"
                >
                    <div class="report-folio-widget">
                        <GenericWidget
                            :aliased-node-data="
                                aliasedNodeDataOf(tile, widget.node.alias)
                            "
                            :card-x-node-x-widget-data="widget"
                            :graph-slug="reportData.context.graph.slug"
                            :mode="VIEW"
                            :node-alias="widget.node.alias"
                        />
                    </div>
                    <template v-if="isEditableTile(tile)">
                        <Button
                            variant="link"
                            size="small"
                            :label="$gettext('Edit')"
                            :aria-label="
                                $gettext(
                                    'Edit %{field}',
                                    {
                                        field: widget.label,
                                    },
                                    true,
                                )
                            "
                            @click="editNode(tile.tileid, widget.node.alias)"
                        />
                        <Button
                            v-if="hasValue(tile, widget.node.alias)"
                            class="report-folio-delete"
                            variant="link"
                            size="small"
                            :label="$gettext('Delete')"
                            :aria-label="
                                $gettext(
                                    'Delete %{field}',
                                    {
                                        field: widget.label,
                                    },
                                    true,
                                )
                            "
                            @click="clearNode(tile.tileid, widget.node.alias)"
                        />
                    </template>
                </div>
            </div>
            <div
                v-if="childAliases.length > 0"
                class="report-folio-children"
            >
                <ReportFolio
                    v-for="childAlias in childAliases"
                    :key="childAlias"
                    :nodegroup-alias="childAlias"
                    :tiles="nodegroupTiles(tile.aliased_data[childAlias])"
                    :parent-tile-id="tile.tileid"
                    :report-data="reportData"
                />
            </div>
        </div>
    </div>
</template>

<style scoped>
.report-folio {
    display: flex;
    flex-direction: column;
    gap: 1.2rem;
}

.report-folio-header {
    display: flex;
    align-items: center;
    gap: 0.8rem;
}

.report-folio-name {
    font-size: 1.8rem;
    font-weight: 600;
}

.report-folio-empty {
    color: var(--p-text-muted-color);
}

.report-folio-tile {
    display: flex;
    flex-direction: column;
    gap: 1.2rem;
    padding: 1.2rem;
    border: 0.1rem solid var(--p-content-border-color);
    border-radius: var(--p-content-border-radius);
}

.report-folio-fields {
    display: flex;
    flex-direction: column;
    gap: 1.4rem;
}

.report-folio-field {
    display: flex;
    align-items: flex-start;
    gap: 0.8rem;
}

.report-folio-widget {
    flex: 1;
    min-inline-size: 0;
}

.report-folio-delete,
.report-folio-delete:not(:disabled):hover,
.report-folio-delete:not(:disabled):active {
    color: var(--p-button-text-danger-color);
}

.report-folio-children {
    display: flex;
    flex-direction: column;
    gap: 1.6rem;
    padding-inline-start: 1.8rem;
}
</style>
