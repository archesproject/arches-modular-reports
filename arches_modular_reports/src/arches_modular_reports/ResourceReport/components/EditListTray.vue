<script setup lang="ts">
import { computed } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";
import ConfirmDialog from "openvue/confirmdialog";
import Message from "openvue/message";
import Tag from "openvue/tag";
import { useConfirm } from "openvue/useconfirm";

import { findTile } from "@/arches_modular_reports/ResourceReport/utils/resource-change-set.ts";
import { tileSummary } from "@/arches_modular_reports/ResourceReport/utils/tiles.ts";

import type {
    ReportData,
    ResourceChange,
} from "@/arches_modular_reports/ResourceReport/types.ts";

const CONFIRM_GROUP = "edit-list-tray";

const { reportData } = defineProps<{
    reportData: ReportData;
}>();

const { $gettext } = useGettext();
const confirm = useConfirm();

const entries = computed(() =>
    reportData.changeSet.pendingChanges.value.map((change) => ({
        change,
        label: entryLabel(change),
        hasNoChanges: !reportData.changeSet.hasChanges(change),
        isConflicting: reportData.changeSet.conflictingChangeIds.value.includes(
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
    const tile = findTile(reportData.resource.aliased_data, tileId);
    if (tile === null) {
        return "";
    }
    return tileSummary(
        tile,
        reportData.nodegroupWidgetConfigs[change.nodegroupAlias],
    );
}

function entryLabel(change: ResourceChange): string {
    return [
        changeTypeLabel(change),
        reportData.nodegroupWidgetConfigs[change.nodegroupAlias].card?.name,
        changedTileSummary(change),
    ]
        .filter(Boolean)
        .join(" · ");
}

function openChange(change: ResourceChange): void {
    const tileId = changedTileId(change);
    if (tileId) {
        reportData.editor.open({
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
            reportData.changeSet.discardAll();
            reportData.editor.close();
        },
    });
}

async function applyAll(): Promise<void> {
    if (await reportData.changeSet.save()) {
        reportData.editor.close();
    }
}
</script>

<template>
    <section class="edit-list-tray">
        <ConfirmDialog :group="CONFIRM_GROUP" />
        <header class="edit-list-tray-header">
            <h3 class="edit-list-tray-title">
                {{
                    $gettext("Edit list (%{count})", {
                        count: String(entries.length),
                    })
                }}
            </h3>
            <Button
                variant="text"
                size="small"
                :label="$gettext('Cancel all')"
                :disabled="reportData.changeSet.isSaving.value"
                @click="confirmCancelAll"
            />
            <Button
                size="small"
                icon="pi pi-check"
                :label="$gettext('Apply all')"
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
                        "Some changes refer to data that no longer exists. Discard them and try again.",
                    )
                }}
            </span>
        </Message>
        <Message
            v-else-if="reportData.changeSet.saveError.value"
            severity="error"
        >
            <span>{{ reportData.changeSet.saveError.value.message }}</span>
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
                    variant="link"
                    size="small"
                    :label="entry.label"
                    :disabled="entry.change.type === 'reorder'"
                    @click="openChange(entry.change)"
                />
                <Tag
                    v-if="entry.hasNoChanges"
                    severity="secondary"
                    :value="$gettext('No changes')"
                />
                <Button
                    icon="pi pi-times"
                    variant="text"
                    size="small"
                    :aria-label="$gettext('Discard change')"
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

.edit-list-tray-entry-conflict {
    border-color: var(--p-form-field-invalid-border-color);
}
</style>
