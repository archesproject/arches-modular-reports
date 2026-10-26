<script setup lang="ts">
import { computed } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";
import Message from "openvue/message";

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
        <header class="editor-panel-header">
            <div class="editor-panel-titles">
                <span class="editor-panel-caption">{{ caption }}</span>
                <h3 class="editor-panel-title">{{ cardName }}</h3>
            </div>
            <Button
                v-if="isMarkedForDeletion"
                icon="pi pi-undo"
                variant="text"
                size="small"
                :label="$gettext('Undo delete')"
                :disabled="reportData.changeSet.isBusy.value"
                @click="undoDelete"
            />
            <Button
                v-else-if="liveTile && !isPendingDelete"
                icon="pi pi-trash"
                variant="text"
                size="small"
                severity="danger"
                :label="$gettext('Delete')"
                :disabled="reportData.changeSet.isBusy.value"
                @click="deleteTile"
            />
            <Button
                icon="pi pi-times"
                variant="text"
                size="small"
                :aria-label="$gettext('Close editor')"
                @click="reportData.editor.close"
            />
        </header>
        <p
            v-if="!liveTile"
            class="editor-panel-empty"
        >
            {{ $gettext("No data to edit.") }}
        </p>
        <template v-else>
            <GenericCard
                :key="`${target.tileId}-${cardMode}`"
                :mode="cardMode"
                :graph-slug="reportData.context.graph.slug"
                :nodegroup-alias="target.nodegroupAlias"
                :tile-data="liveTile"
                :resource-instance-id="reportData.resource.resourceinstanceid"
                :selected-node-alias="selectedNodeAlias"
                :should-show-form-buttons="false"
                :should-show-card-name="false"
                @update:tile-data="onUpdateTileData"
            />
            <Message
                v-if="isPendingDelete"
                severity="warn"
            >
                <span>{{ deletionMessage }}</span>
            </Message>
            <footer
                v-else-if="addableChildAliases.length > 0"
                class="editor-panel-footer"
            >
                <div
                    v-for="childAlias in addableChildAliases"
                    :key="childAlias"
                    class="editor-panel-add-row"
                >
                    <span>{{ childCardName(childAlias) }}</span>
                    <Button
                        icon="pi pi-plus"
                        variant="text"
                        size="small"
                        :label="
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
        </template>
    </section>
</template>

<style scoped>
.editor-panel {
    display: flex;
    flex-direction: column;
    gap: 1.6rem;
    padding: 1.6rem;
}

.editor-panel-header {
    display: flex;
    align-items: flex-start;
    gap: 0.8rem;
}

.editor-panel-titles {
    display: flex;
    flex: 1;
    flex-direction: column;
    gap: 0.4rem;
    min-inline-size: 0;
}

.editor-panel-caption {
    color: var(--p-text-muted-color);
    font-size: 1.2rem;
    letter-spacing: 0.08rem;
    text-transform: uppercase;
}

.editor-panel-title {
    margin: 0;
    font-size: 1.8rem;
    font-weight: 600;
}

.editor-panel-empty {
    margin: 0;
    color: var(--p-text-muted-color);
}

.editor-panel-footer {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    padding-block-start: 1.2rem;
    border-block-start: 0.1rem solid var(--p-content-border-color);
}

.editor-panel-add-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.8rem;
}
</style>
