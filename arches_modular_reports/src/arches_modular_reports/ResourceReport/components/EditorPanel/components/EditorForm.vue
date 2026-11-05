<script setup lang="ts">
import { computed } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";

import GenericCard from "@/arches_vue_components/generics/GenericCard/GenericCard.vue";

import { EDIT, VIEW } from "@/arches_vue_components/widgets/constants.ts";
import {
    childNodegroupAliases,
    nodegroupLineage,
} from "@/arches_modular_reports/ResourceReport/utils/graph-nodes.ts";
import { useReportData } from "@/arches_modular_reports/ResourceReport/composables/useReportData.ts";
import { findTile } from "@/arches_modular_reports/ResourceReport/utils/resource-change-set.ts";
import {
    canAddTile,
    nodegroupTiles,
} from "@/arches_modular_reports/ResourceReport/utils/tiles.ts";

import type { AliasedTileData } from "@/arches_vue_components/types.ts";
import type { EditTileRequest } from "@/arches_modular_reports/ResourceReport/types.ts";

const { target } = defineProps<{
    target: EditTileRequest;
}>();

const { $gettext } = useGettext();
const reportData = useReportData();

const liveTile = computed(() =>
    findTile(reportData.value.resource.aliased_data, target.tileId),
);

const nodegroupWidgetConfig = computed(
    () => reportData.value.nodegroupWidgetConfigs[target.nodegroupAlias],
);

const cardName = computed(() => nodegroupWidgetConfig.value.card?.name ?? "");

const selectedNodeAlias = computed(() => {
    if (target.nodeAlias) {
        return target.nodeAlias;
    }
    const firstVisibleWidget =
        nodegroupWidgetConfig.value.card_x_node_x_widgets.find(
            (widget) => widget.visible,
        );
    return firstVisibleWidget?.node.alias ?? null;
});

const caption = computed(() => {
    const topLevelAlias = nodegroupLineage(
        reportData.value.nodegroupWidgetConfigs,
        target.nodegroupAlias,
    ).at(-1);
    if (topLevelAlias && reportData.value.folioLocations[topLevelAlias]) {
        return $gettext(
            "Editor · %{location}",
            {
                location: reportData.value.folioLocations[topLevelAlias],
            },
            true,
        );
    }
    return $gettext("Editor");
});

const isMarkedForDeletion = computed(
    () =>
        reportData.value.changeSet.changeTypeForTile(target.tileId) ===
        "delete",
);

const isPendingDelete = computed(() =>
    reportData.value.changeSet.isPendingDelete(target.tileId),
);

const cardMode = computed(() => {
    if (isPendingDelete.value) {
        return VIEW;
    }
    return EDIT;
});

const childAliases = computed(() =>
    childNodegroupAliases(
        reportData.value.nodegroupWidgetConfigs,
        target.nodegroupAlias,
    ),
);

const addableChildAliases = computed(() =>
    childAliases.value.filter((childAlias) =>
        canAddTile(
            reportData.value.nodegroupWidgetConfigs[childAlias],
            nodegroupTiles(liveTile.value?.aliased_data[childAlias]).length,
            target.tileId,
            reportData.value.changeSet,
        ),
    ),
);

const deletionMessage = computed(() => {
    const hasChildData = childAliases.value.some(
        (childAlias) =>
            nodegroupTiles(liveTile.value?.aliased_data[childAlias]).length > 0,
    );
    if (hasChildData) {
        return $gettext(
            "This entry and all its related child data will be removed when you Apply all edits.",
        );
    }
    return $gettext("This entry will be removed when you Apply all edits.");
});

function childCardName(childAlias: string): string {
    return reportData.value.nodegroupWidgetConfigs[childAlias].card?.name ?? "";
}

function onUpdateTileData(tileData: AliasedTileData): void {
    reportData.value.changeSet.editTile(
        target.nodegroupAlias,
        target.tileId,
        tileData.aliased_data,
    );
}

async function addChild(childAlias: string): Promise<void> {
    const tileId = await reportData.value.changeSet.addTile(
        childAlias,
        target.tileId,
    );
    if (tileId !== null) {
        reportData.value.editor.open({ nodegroupAlias: childAlias, tileId });
    }
}

function deleteTile(): void {
    reportData.value.changeSet.deleteTile(target.nodegroupAlias, target.tileId);
}

function undoDelete(): void {
    reportData.value.changeSet.undoDelete(target.tileId);
}
</script>

<template>
    <section class="editor-panel">
        <header class="editor-panel-bar">
            <span class="editor-panel-caption">{{ caption }}</span>
            <Button
                class="editor-panel-close"
                variant="text"
                severity="secondary"
                size="small"
                icon="pi pi-times"
                icon-pos="right"
                :label="$gettext('Close editor')"
                @click="reportData.editor.close"
            />
        </header>
        <div class="editor-panel-body">
            <p
                v-if="!liveTile"
                class="editor-panel-empty"
            >
                {{ $gettext("No data to edit.") }}
            </p>
            <article
                v-else
                class="editor-panel-card"
                :class="{ 'editor-panel-card-deleted': isPendingDelete }"
            >
                <header class="editor-panel-card-header">
                    <h3 class="editor-panel-title">{{ cardName }}</h3>
                    <Button
                        v-if="!isPendingDelete"
                        class="editor-panel-delete"
                        variant="outlined"
                        severity="danger"
                        size="small"
                        :label="$gettext('Delete')"
                        :disabled="reportData.changeSet.isBusy.value"
                        @click="deleteTile"
                    />
                </header>
                <div class="editor-panel-card-body">
                    <GenericCard
                        :key="`${target.tileId}-${cardMode}`"
                        :mode="cardMode"
                        :graph-slug="reportData.context.graph.slug"
                        :nodegroup-alias="target.nodegroupAlias"
                        :tile-data="liveTile"
                        :resource-instance-id="
                            reportData.resource.resourceinstanceid
                        "
                        :selected-node-alias="selectedNodeAlias"
                        :should-show-form-buttons="false"
                        :should-show-card-name="false"
                        @update:tile-data="onUpdateTileData"
                    />
                </div>
                <footer
                    v-if="isPendingDelete"
                    class="editor-panel-card-footer"
                >
                    <div class="editor-panel-footer-row">
                        <span class="editor-panel-delete-note">
                            {{ deletionMessage }}
                        </span>
                        <Button
                            v-if="isMarkedForDeletion"
                            class="editor-panel-footer-action"
                            variant="outlined"
                            size="small"
                            :label="$gettext('Undo delete')"
                            :disabled="reportData.changeSet.isBusy.value"
                            @click="undoDelete"
                        />
                    </div>
                </footer>
                <footer
                    v-else-if="addableChildAliases.length > 0"
                    class="editor-panel-card-footer"
                >
                    <div
                        v-for="childAlias in addableChildAliases"
                        :key="childAlias"
                        class="editor-panel-footer-row"
                    >
                        <span class="editor-panel-add-note">
                            {{
                                $gettext(
                                    "You can add %{name} related to this entry.",
                                    {
                                        name: childCardName(childAlias),
                                    },
                                    true,
                                )
                            }}
                        </span>
                        <Button
                            class="editor-panel-footer-action"
                            variant="outlined"
                            size="small"
                            :label="$gettext('Add')"
                            :aria-label="
                                $gettext(
                                    'Add %{name}',
                                    {
                                        name: childCardName(childAlias),
                                    },
                                    true,
                                )
                            "
                            :disabled="reportData.changeSet.isBusy.value"
                            @click="addChild(childAlias)"
                        />
                    </div>
                </footer>
            </article>
        </div>
    </section>
</template>

<style scoped>
.editor-panel {
    display: flex;
    flex: 1;
    flex-direction: column;
    min-block-size: 0;
}

.editor-panel-bar {
    display: flex;
    flex-shrink: 0;
    align-items: center;
    justify-content: space-between;
    gap: 1.2rem;
    padding-block: 0.7rem 0.8rem;
    padding-inline: 1.6rem;
    border-block-end: 0.1rem solid var(--resource-report-bar-border-color);
    background: var(--resource-report-bar-background);
}

.editor-panel-caption {
    min-inline-size: 0;
    overflow: hidden;
    color: var(--p-text-muted-color);
    font-size: 1.2rem;
    font-weight: 700;
    letter-spacing: 0.07rem;
    text-overflow: ellipsis;
    text-transform: uppercase;
    white-space: nowrap;
}

.editor-panel-bar .editor-panel-close {
    --p-button-label-font-weight: 400;
    flex-shrink: 0;
    gap: 0.6rem;
    padding-block: 0.4rem;
    padding-inline: 0.8rem;
    border: none;
    border-radius: 0.4rem;
    color: var(--p-text-muted-color);
    font-size: 1.3rem;
    line-height: 1;
}

.editor-panel-bar .editor-panel-close:not(:disabled):hover {
    background: var(--resource-report-caption-background);
    color: var(--p-text-color);
}

.editor-panel-body {
    flex: 1;
    min-block-size: 0;
    padding: 2.4rem;
    overflow: auto;
}

.editor-panel-empty {
    margin: 0;
    color: var(--p-text-muted-color);
    font-style: italic;
}

.editor-panel-card {
    border: 0.1rem solid var(--p-content-border-color);
    border-radius: 0.2rem;
    background: var(--p-content-background);
}

.editor-panel-card-deleted {
    border-color: var(--resource-report-deleted-color);
}

.editor-panel-card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1.2rem;
    padding-block: 1.8rem;
    padding-inline: 2.4rem;
    border-block-end: 0.1rem solid var(--p-content-border-color);
}

.editor-panel-title {
    margin: 0;
    font-size: 1.5rem;
    font-weight: 700;
    line-height: 1.5;
}

.editor-panel-card-header .editor-panel-delete {
    --p-button-label-font-weight: 400;
    flex-shrink: 0;
    padding-block: 0.6rem;
    padding-inline: 1.2rem;
    border-color: var(--resource-report-deleted-color);
    border-radius: 0.2rem;
    background: var(--resource-report-deleted-background);
    color: var(--resource-report-deleted-color);
    font-size: 1.3rem;
    line-height: 1.2;
}

.editor-panel-card-body {
    --p-inputtext-padding-x: 1.1rem;
    --p-inputtext-padding-y: 0.8rem;
    --p-inputtext-border-color: var(--p-content-border-color);
    --p-inputtext-border-radius: 0.6rem;
    --p-select-padding-x: 1.1rem;
    --p-select-padding-y: 0.8rem;
    --p-select-border-color: var(--p-content-border-color);
    --p-select-border-radius: 0.6rem;
    --p-treeselect-padding-x: 1.1rem;
    --p-treeselect-padding-y: 0.8rem;
    --p-treeselect-border-color: var(--p-content-border-color);
    --p-treeselect-border-radius: 0.6rem;
    padding: 2.4rem;
}

.editor-panel-card-body :deep(.p-form) {
    gap: 1.8rem;
}

.editor-panel-card-body :deep(.widget-label) {
    margin-block-end: 0.5rem;
    color: var(--p-text-muted-color);
    font-size: 1.25rem;
    font-weight: 600;
}

.editor-panel-card-body :deep(.p-inputtext),
.editor-panel-card-body :deep(.p-select-label),
.editor-panel-card-body :deep(.p-treeselect-label) {
    font-size: 1.35rem;
    line-height: 1.2;
}

.editor-panel-card-footer {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    padding-block: 1.6rem;
    padding-inline: 2.4rem;
    border-block-start: 0.1rem solid var(--p-content-border-color);
    background: var(--resource-report-aside-background);
}

.editor-panel-card-deleted .editor-panel-card-footer {
    background: var(--resource-report-deleted-background);
}

.editor-panel-footer-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1.2rem;
}

.editor-panel-add-note {
    color: var(--p-text-muted-color);
    font-size: 1.25rem;
}

.editor-panel-delete-note {
    color: var(--resource-report-deleted-color);
    font-size: 1.25rem;
    font-weight: 600;
}

.editor-panel-footer-row .editor-panel-footer-action {
    --p-button-label-font-weight: 400;
    flex-shrink: 0;
    padding-block: 0.4rem;
    padding-inline: 1rem;
    border-color: var(--resource-report-accent-color);
    border-radius: 0.2rem;
    background: var(--resource-report-accent-background);
    color: var(--resource-report-accent-color);
    font-size: 1.3rem;
}
</style>
