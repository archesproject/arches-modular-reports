<script setup lang="ts">
import { computed } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";
import ConfirmDialog from "openvue/confirmdialog";
import Message from "openvue/message";
import { useConfirm } from "openvue/useconfirm";

import { useReportData } from "@/arches_modular_reports/ResourceReport/composables/useReportData.ts";
import { findTile } from "@/arches_modular_reports/ResourceReport/utils/resource-change-set.ts";
import { tileSummary } from "@/arches_modular_reports/ResourceReport/utils/tiles.ts";

import type {
    ComponentNode,
    ResourceChange,
} from "@/arches_modular_reports/ResourceReport/types.ts";

const CONFIRM_GROUP = "edit-list-tray";

defineProps<{
    component: ComponentNode;
}>();

const { $gettext } = useGettext();
const reportData = useReportData();
const confirm = useConfirm();

const hasPendingChanges = computed(
    () => reportData.value.changeSet.pendingChanges.value.length > 0,
);

const entries = computed(() =>
    reportData.value.changeSet.pendingChanges.value.map((change) => ({
        change,
        changeTypeLabel: changeTypeLabel(change),
        cardName:
            reportData.value.nodegroupWidgetConfigs[change.nodegroupAlias].card
                ?.name,
        tileSummary: changedTileSummary(change),
        isConflicting:
            reportData.value.changeSet.conflictingChangeIds.value.includes(
                change.id,
            ),
    })),
);

function changeTypeLabel(change: ResourceChange): string {
    if (change.type === "add") {
        return $gettext("Added");
    }
    if (change.type === "edit") {
        return $gettext("Edited");
    }
    if (change.type === "delete") {
        return $gettext("Deleted");
    }
    return $gettext("Reordered");
}

function changedTileId(change: ResourceChange): string | null {
    if (change.type === "add") {
        return change.tile.tileid;
    }
    if (change.type === "reorder") {
        return null;
    }
    return change.tileId;
}

function changedTileSummary(change: ResourceChange): string {
    const tileId = changedTileId(change);
    if (tileId === null) {
        return "";
    }
    const tile = findTile(reportData.value.resource.aliased_data, tileId);
    if (tile === null) {
        return "";
    }
    return tileSummary(
        tile,
        reportData.value.nodegroupWidgetConfigs[change.nodegroupAlias],
    );
}

function openChange(change: ResourceChange): void {
    const tileId = changedTileId(change);
    if (tileId) {
        reportData.value.editor.open({
            nodegroupAlias: change.nodegroupAlias,
            tileId,
        });
    }
}

function confirmCancelAll(): void {
    confirm.require({
        group: CONFIRM_GROUP,
        header: $gettext("Discard all changes?"),
        message: $gettext(
            "Every pending change will be discarded. This cannot be undone.",
        ),
        acceptLabel: $gettext("Discard all"),
        rejectLabel: $gettext("Keep editing"),
        accept: () => {
            reportData.value.changeSet.discardAll();
            reportData.value.editor.close();
        },
    });
}

async function applyAll(): Promise<void> {
    const isSaved = await reportData.value.changeSet.save();
    if (
        isSaved &&
        reportData.value.changeSet.pendingChanges.value.length === 0
    ) {
        reportData.value.editor.close();
    }
}
</script>

<template>
    <section
        v-if="hasPendingChanges"
        class="edit-list-tray"
    >
        <ConfirmDialog :group="CONFIRM_GROUP" />
        <header class="edit-list-tray-header">
            <h3 class="edit-list-tray-title">
                {{ $gettext("Edit List") }}
            </h3>
            <Button
                variant="text"
                size="small"
                :label="$gettext('Cancel all edits')"
                :disabled="reportData.changeSet.isBusy.value"
                @click="confirmCancelAll"
            />
            <Button
                size="small"
                icon="pi pi-check"
                :label="$gettext('Apply all edits')"
                :loading="reportData.changeSet.isSaving.value"
                @click="applyAll"
            />
        </header>
        <Message
            v-if="reportData.changeSet.conflictingChangeIds.value.length > 0"
            severity="error"
        >
            <span>
                {{
                    $gettext(
                        "Some changes conflict with newer data. Apply again to keep yours, or discard them.",
                    )
                }}
            </span>
        </Message>
        <Message
            v-else-if="reportData.changeSet.saveError.value"
            severity="error"
        >
            <span>
                {{
                    $gettext(
                        "Unable to apply your edits: %{message}",
                        {
                            message:
                                reportData.changeSet.saveError.value.message,
                        },
                        true,
                    )
                }}
            </span>
        </Message>
        <ul class="edit-list-tray-entries">
            <li
                v-for="entry in entries"
                :key="entry.change.id"
                class="edit-list-tray-entry"
                :class="{
                    'edit-list-tray-entry-conflict': entry.isConflicting,
                }"
            >
                <Button
                    class="edit-list-tray-entry-open"
                    variant="link"
                    size="small"
                    :disabled="entry.change.type === 'reorder'"
                    @click="openChange(entry.change)"
                >
                    <span class="edit-list-tray-entry-type">
                        {{ entry.changeTypeLabel }}
                    </span>
                    <span v-if="entry.cardName">{{ entry.cardName }}</span>
                    <span v-if="entry.tileSummary">
                        {{ entry.tileSummary }}
                    </span>
                </Button>
                <Button
                    icon="pi pi-times"
                    variant="text"
                    size="small"
                    :aria-label="$gettext('Discard change')"
                    :disabled="reportData.changeSet.isBusy.value"
                    @click="reportData.changeSet.discardChange(entry.change.id)"
                />
            </li>
        </ul>
    </section>
</template>

<style scoped>
.edit-list-tray {
    display: flex;
    flex-direction: column;
    gap: 0.8rem;
    padding-block: 0.8rem;
    padding-inline: 1.6rem;
    border-block-start: 0.1rem solid var(--p-content-border-color);
    background: var(--p-content-hover-background);
    color: var(--p-text-color);
}

.edit-list-tray-header {
    display: flex;
    align-items: center;
    gap: 0.8rem;
}

.edit-list-tray-title {
    flex: 1;
    margin: 0;
    font-size: 1.4rem;
    font-weight: 600;
}

.edit-list-tray-entries {
    display: flex;
    flex-wrap: wrap;
    gap: 0.6rem;
    margin: 0;
    padding: 0;
    list-style: none;
}

.edit-list-tray-entry {
    display: flex;
    align-items: center;
    gap: 0.2rem;
    padding-inline-start: 0.4rem;
    border: 0.1rem solid var(--p-content-border-color);
    border-radius: var(--p-content-border-radius);
    background: var(--p-content-background);
}

.edit-list-tray-entry-open {
    gap: 0.4rem;
}

.edit-list-tray-entry-type {
    font-weight: 600;
}

.edit-list-tray-entry-conflict {
    border-color: var(--p-form-field-invalid-border-color);
}
</style>
