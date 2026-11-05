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
        description: changeDescription(change),
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

function changeDescription(change: ResourceChange): string {
    const cardName =
        reportData.value.nodegroupWidgetConfigs[change.nodegroupAlias].card
            ?.name ?? "";
    return [cardName, changedTileSummary(change)]
        .filter((part) => part !== "")
        .join(" · ");
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
        <div class="edit-list-tray-changes">
            <h3 class="edit-list-tray-title">
                {{ $gettext("Edit List") }}
            </h3>
            <Message
                v-if="
                    reportData.changeSet.conflictingChangeIds.value.length > 0
                "
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
                                    reportData.changeSet.saveError.value
                                        .message,
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
                    :class="[
                        `edit-list-tray-entry-${entry.change.type}`,
                        {
                            'edit-list-tray-entry-conflict':
                                entry.isConflicting,
                        },
                    ]"
                >
                    <Button
                        class="edit-list-tray-entry-open"
                        variant="text"
                        size="small"
                        :title="entry.description"
                        :disabled="entry.change.type === 'reorder'"
                        @click="openChange(entry.change)"
                    >
                        <i
                            v-if="entry.isConflicting"
                            class="pi pi-exclamation-triangle"
                            role="img"
                            :aria-label="$gettext('Conflicts with newer data')"
                        />
                        <span class="edit-list-tray-entry-type">
                            {{ entry.changeTypeLabel }}
                        </span>
                        <span class="edit-list-tray-entry-description">
                            {{ entry.description }}
                        </span>
                    </Button>
                    <Button
                        class="edit-list-tray-entry-discard"
                        icon="pi pi-times"
                        variant="text"
                        size="small"
                        :aria-label="$gettext('Discard change')"
                        :disabled="reportData.changeSet.isBusy.value"
                        @click="
                            reportData.changeSet.discardChange(entry.change.id)
                        "
                    />
                </li>
            </ul>
        </div>
        <div class="edit-list-tray-actions">
            <Button
                class="edit-list-tray-action edit-list-tray-cancel"
                severity="secondary"
                :label="$gettext('Cancel all edits')"
                :disabled="reportData.changeSet.isBusy.value"
                @click="confirmCancelAll"
            />
            <Button
                class="edit-list-tray-action"
                :label="$gettext('Apply all edits')"
                :loading="reportData.changeSet.isSaving.value"
                @click="applyAll"
            />
        </div>
    </section>
</template>

<style scoped>
.edit-list-tray {
    display: flex;
    flex-direction: column;
    border-block-start: 0.2rem solid var(--resource-report-bar-border-color);
    background: var(--p-content-background);
    color: var(--p-text-color);
}

.edit-list-tray-changes {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
    padding-block: 0.6rem 2.4rem;
    padding-inline: 1.4rem;
}

.edit-list-tray-title {
    margin: 0;
    color: var(--p-text-muted-color);
    font-size: 1.2rem;
    font-weight: 700;
    letter-spacing: 0.08rem;
    line-height: 1.5;
    text-transform: uppercase;
}

.edit-list-tray-entries {
    display: flex;
    flex-wrap: wrap;
    gap: 0.2rem;
    margin: 0;
    padding: 0;
    list-style: none;
}

.edit-list-tray-entry {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    max-inline-size: 100%;
    padding-block: 0.4rem;
    padding-inline: 0.8rem;
    border-radius: 1rem;
    background: var(--resource-report-accent-background);
    color: var(--resource-report-accent-color);
}

.edit-list-tray-entry:hover {
    filter: brightness(0.9);
}

.edit-list-tray-entry-edit {
    background: var(--resource-report-edited-background);
    color: var(--resource-report-edited-color);
}

.edit-list-tray-entry-delete {
    background: var(--resource-report-deleted-background);
    color: var(--resource-report-deleted-color);
}

.edit-list-tray-entry-reorder {
    background: var(--resource-report-caption-background);
    color: var(--p-text-muted-color);
}

.edit-list-tray-entry-conflict {
    outline: 0.1rem solid var(--p-form-field-invalid-border-color);
}

.edit-list-tray-entry .edit-list-tray-entry-open,
.edit-list-tray-entry .edit-list-tray-entry-discard {
    padding: 0;
    border: none;
    background: transparent;
    color: inherit;
    font-size: 1.2rem;
    font-weight: 600;
}

.edit-list-tray-entry .edit-list-tray-entry-open {
    gap: 0.4rem;
    max-inline-size: 22rem;
    min-inline-size: 0;
}

.edit-list-tray-entry .edit-list-tray-entry-open:not(:disabled):hover,
.edit-list-tray-entry .edit-list-tray-entry-discard:not(:disabled):hover {
    background: transparent;
    color: inherit;
}

.edit-list-tray-entry .edit-list-tray-entry-discard {
    padding-inline-start: 0.2rem;
    opacity: 0.55;
}

.edit-list-tray-entry .edit-list-tray-entry-discard:not(:disabled):hover {
    opacity: 1;
}

.edit-list-tray-entry-type {
    flex-shrink: 0;
    font-size: 1.1rem;
    font-weight: 700;
    letter-spacing: 0.06rem;
    opacity: 0.75;
    text-transform: uppercase;
}

.edit-list-tray-entry-description {
    min-inline-size: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.edit-list-tray-actions {
    display: flex;
    justify-content: flex-end;
    gap: 0.8rem;
    padding: 1.5rem;
    border-block-start: 0.1rem solid var(--resource-report-bar-border-color);
    background: var(--resource-report-bar-background);
}

.edit-list-tray-actions .edit-list-tray-action {
    --p-button-label-font-weight: 600;
    padding-block: 0.7rem;
    padding-inline: 1.6rem;
    border-radius: 0.5rem;
    font-size: 1.3rem;
    line-height: 1.2;
}

.edit-list-tray-actions .edit-list-tray-cancel {
    border-color: var(--resource-report-bar-border-color);
    color: var(--p-text-color);
}
</style>
