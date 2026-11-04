<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";
import ConfirmDialog from "openvue/confirmdialog";
import Message from "openvue/message";
import { useConfirm } from "openvue/useconfirm";

import { useReportData } from "@/arches_modular_reports/ResourceReport/composables/useReportData.ts";
import { findTile } from "@/arches_modular_reports/ResourceReport/utils/resource-change-set.ts";
import { tileSummary } from "@/arches_modular_reports/ResourceReport/utils/tiles.ts";

import type {
    ChangeConflict,
    ComponentNode,
    ResourceChange,
} from "@/arches_modular_reports/ResourceReport/types.ts";

const CONFIRM_GROUP = "edit-list-tray";

defineProps<{
    component: ComponentNode;
}>();

const { $gettext, $ngettext } = useGettext();
const reportData = useReportData();
const confirm = useConfirm();

const conflictSummary = ref<HTMLElement | null>(null);

const hasPendingChanges = computed(
    () => reportData.value.changeSet.pendingChanges.value.length > 0,
);

const conflictingChangeIds = computed(
    () =>
        new Set(
            reportData.value.changeSet.conflicts.value.map(
                (conflict) => conflict.changeId,
            ),
        ),
);

const entries = computed(() =>
    reportData.value.changeSet.pendingChanges.value.map((change) => ({
        change,
        changeTypeLabel: changeTypeLabel(change),
        description: changeDescription(change),
        isConflicting: conflictingChangeIds.value.has(change.id),
    })),
);

const conflictItems = computed(() =>
    reportData.value.changeSet.conflicts.value.map(describeConflict),
);

const hasKeepableConflict = computed(() =>
    conflictItems.value.some((item) => item.canKeepMine),
);

const conflictHeading = computed(() =>
    $ngettext(
        "Nothing was saved. %{count} of your changes conflicts with newer data.",
        "Nothing was saved. %{count} of your changes conflict with newer data.",
        conflictItems.value.length,
        { count: String(conflictItems.value.length) },
    ),
);

const liveAnnouncement = computed(() => {
    if (conflictItems.value.length > 0) {
        return `${conflictHeading.value} ${$gettext("Review each one below, then apply your edits again.")}`;
    }
    if (reportData.value.changeSet.conflictsResolved.value) {
        return $gettext(
            "All conflicts are resolved. Apply all edits to save your changes.",
        );
    }
    return "";
});

watch(
    () => reportData.value.changeSet.conflicts.value,
    async (conflicts, previousConflicts) => {
        if (conflicts.length > 0 && previousConflicts.length === 0) {
            await nextTick();
            conflictSummary.value?.focus();
        }
    },
);

function nodeLabel(nodeAlias: string): string {
    return reportData.value.graphNodesByAlias[nodeAlias]?.label ?? nodeAlias;
}

function nodegroupLabel(nodegroupAlias: string): string {
    return (
        reportData.value.nodegroupWidgetConfigs[nodegroupAlias]?.card?.name ??
        nodegroupAlias
    );
}

function displayOrEmpty(value: string | null | undefined): string {
    return value ? value : $gettext("(empty)");
}

interface ConflictRow {
    field: string;
    mine: string;
    theirs: string;
}

interface ConflictViewModel {
    conflict: ChangeConflict;
    nodegroup: string;
    rows: ConflictRow[];
    message: string;
    keepLabel: string;
    keepAriaLabel: string;
    discardLabel: string;
    discardAriaLabel: string;
    canKeepMine: boolean;
    note: string;
}

function describeConflict(conflict: ChangeConflict): ConflictViewModel {
    const change = reportData.value.changeSet.pendingChanges.value.find(
        (pendingChange) => pendingChange.id === conflict.changeId,
    );
    const nodegroup = nodegroupLabel(conflict.nodegroupAlias);
    const keepLabel = $gettext("Keep mine");
    const discardLabel = $gettext("Discard");
    const base: ConflictViewModel = {
        conflict,
        nodegroup,
        rows: [],
        message: "",
        keepLabel,
        keepAriaLabel: "",
        discardLabel,
        discardAriaLabel: $gettext(
            "Discard my change to %{nodegroup}",
            { nodegroup },
            true,
        ),
        canKeepMine: false,
        note: "",
    };

    if (conflict.reason === "modified") {
        const nodeAliases = Object.keys(conflict.nodes ?? {});
        const fields = nodeAliases.map(nodeLabel).join(", ");
        const rows = nodeAliases.map((nodeAlias) => ({
            field: nodeLabel(nodeAlias),
            mine: displayOrEmpty(
                change?.type === "edit"
                    ? change.aliasedData[nodeAlias]?.display_value
                    : null,
            ),
            theirs: displayOrEmpty(conflict.nodes?.[nodeAlias].currentDisplay),
        }));
        return {
            ...base,
            rows,
            message: $gettext(
                "Someone else changed %{fields} in %{nodegroup} after you started editing.",
                { fields, nodegroup },
                true,
            ),
            keepLabel,
            keepAriaLabel: $gettext(
                "Keep my value for %{fields} and overwrite theirs",
                { fields },
                true,
            ),
            discardLabel: $gettext("Use theirs"),
            discardAriaLabel: $gettext(
                "Use their value for %{fields} and drop my change to it",
                { fields },
                true,
            ),
            canKeepMine: true,
        };
    }
    if (conflict.reason === "deleted") {
        const summary = conflict.tileSnapshot
            ? tileSummary(
                  conflict.tileSnapshot,
                  reportData.value.nodegroupWidgetConfigs[
                      conflict.nodegroupAlias
                  ],
              )
            : "";
        return {
            ...base,
            message: $gettext(
                "This %{nodegroup} entry was deleted by someone else.",
                { nodegroup },
                true,
            ),
            note: summary,
            keepLabel: $gettext("Restore with my changes"),
            keepAriaLabel: $gettext(
                "Restore the deleted %{nodegroup} entry with my changes",
                { nodegroup },
                true,
            ),
            canKeepMine: conflict.tileSnapshot !== undefined,
        };
    }
    if (conflict.reason === "slot_taken") {
        return {
            ...base,
            message: $gettext(
                "Someone else already added %{nodegroup}.",
                { nodegroup },
                true,
            ),
            keepLabel: $gettext("Replace with mine"),
            keepAriaLabel: $gettext(
                "Replace the existing %{nodegroup} with my version",
                { nodegroup },
                true,
            ),
            canKeepMine: true,
        };
    }
    return {
        ...base,
        message: $gettext(
            "The entry this %{nodegroup} belonged to was deleted by someone else.",
            { nodegroup },
            true,
        ),
        note: $gettext(
            "It can only be discarded. If you restore the deleted entry from this list, it becomes savable again.",
        ),
    };
}

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
            <div
                class="edit-list-tray-sr-only"
                role="status"
                aria-live="polite"
            >
                {{ liveAnnouncement }}
            </div>
            <section
                v-if="conflictItems.length > 0"
                class="edit-list-tray-conflicts"
                aria-labelledby="edit-list-tray-conflict-heading"
            >
                <Message severity="error">
                    <div
                        ref="conflictSummary"
                        class="edit-list-tray-conflict-summary"
                        tabindex="-1"
                    >
                        <h4
                            id="edit-list-tray-conflict-heading"
                            class="edit-list-tray-conflict-heading"
                        >
                            {{ conflictHeading }}
                        </h4>
                        <p class="edit-list-tray-conflict-help">
                            {{
                                $gettext(
                                    "Your changes are still in the list. Choose what to do with each conflict, then apply your edits again.",
                                )
                            }}
                        </p>
                    </div>
                </Message>
                <div
                    v-if="conflictItems.length > 1"
                    class="edit-list-tray-conflict-bulk"
                >
                    <Button
                        v-if="hasKeepableConflict"
                        size="small"
                        :label="$gettext('Keep all mine')"
                        :disabled="reportData.changeSet.isBusy.value"
                        @click="reportData.changeSet.keepAllMine()"
                    />
                    <Button
                        size="small"
                        variant="outlined"
                        :label="$gettext('Discard all conflicting')"
                        :disabled="reportData.changeSet.isBusy.value"
                        @click="reportData.changeSet.discardAllConflicting()"
                    />
                </div>
                <ul class="edit-list-tray-conflict-list">
                    <li
                        v-for="item in conflictItems"
                        :key="item.conflict.changeId"
                        class="edit-list-tray-conflict"
                    >
                        <p class="edit-list-tray-conflict-message">
                            <i
                                class="pi pi-exclamation-triangle"
                                aria-hidden="true"
                            />
                            <span>{{ item.message }}</span>
                        </p>
                        <p
                            v-if="item.note"
                            class="edit-list-tray-conflict-note"
                        >
                            {{ item.note }}
                        </p>
                        <dl
                            v-for="row in item.rows"
                            :key="row.field"
                            class="edit-list-tray-conflict-values"
                        >
                            <dt>{{ row.field }}</dt>
                            <dd>
                                <span
                                    class="edit-list-tray-conflict-value-label"
                                >
                                    {{ $gettext("Their value:") }}
                                </span>
                                {{ row.theirs }}
                            </dd>
                            <dd>
                                <span
                                    class="edit-list-tray-conflict-value-label"
                                >
                                    {{ $gettext("Your value:") }}
                                </span>
                                {{ row.mine }}
                            </dd>
                        </dl>
                        <div class="edit-list-tray-conflict-actions">
                            <Button
                                v-if="item.canKeepMine"
                                size="small"
                                :label="item.keepLabel"
                                :aria-label="item.keepAriaLabel"
                                :disabled="reportData.changeSet.isBusy.value"
                                @click="
                                    reportData.changeSet.keepMine(
                                        item.conflict.changeId,
                                    )
                                "
                            />
                            <Button
                                size="small"
                                variant="outlined"
                                :label="item.discardLabel"
                                :aria-label="item.discardAriaLabel"
                                :disabled="reportData.changeSet.isBusy.value"
                                @click="
                                    reportData.changeSet.useTheirs(
                                        item.conflict.changeId,
                                    )
                                "
                            />
                        </div>
                    </li>
                </ul>
            </section>
            <Message
                v-else-if="reportData.changeSet.conflictsResolved.value"
                severity="success"
            >
                <span>
                    {{
                        $gettext(
                            "All conflicts are resolved. Apply all edits to save your changes.",
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
                        <span
                            v-if="entry.isConflicting"
                            class="edit-list-tray-entry-conflict-flag"
                        >
                            <i
                                class="pi pi-exclamation-triangle"
                                aria-hidden="true"
                            />
                            {{ $gettext("Conflict") }}
                        </span>
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

.edit-list-tray-entry-conflict-flag {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    font-size: 1.2rem;
    font-weight: 600;
    color: var(--p-form-field-invalid-border-color);
}

.edit-list-tray-sr-only {
    position: absolute;
    inline-size: 0.1rem;
    block-size: 0.1rem;
    overflow: hidden;
    clip-path: inset(50%);
    white-space: nowrap;
}

.edit-list-tray-conflicts {
    display: flex;
    flex-direction: column;
    gap: 0.8rem;
}

.edit-list-tray-conflict-summary:focus-visible {
    outline: 0.2rem solid var(--p-focus-ring-color);
    outline-offset: 0.2rem;
}

.edit-list-tray-conflict-heading {
    margin: 0;
    font-size: 1.4rem;
    font-weight: 600;
}

.edit-list-tray-conflict-help {
    margin: 0;
    margin-block-start: 0.2rem;
}

.edit-list-tray-conflict-bulk,
.edit-list-tray-conflict-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 0.6rem;
}

.edit-list-tray-conflict-list {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
    margin: 0;
    padding: 0;
    list-style: none;
}

.edit-list-tray-conflict {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
    padding: 0.8rem 1.2rem;
    border: 0.1rem solid var(--p-form-field-invalid-border-color);
    border-radius: var(--p-content-border-radius);
    background: var(--p-content-background);
}

.edit-list-tray-conflict-message {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin: 0;
    font-weight: 600;
}

.edit-list-tray-conflict-note {
    margin: 0;
    color: var(--p-text-muted-color);
}

.edit-list-tray-conflict-values {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
    margin: 0;
}

.edit-list-tray-conflict-values dt {
    font-weight: 600;
}

.edit-list-tray-conflict-values dd {
    margin: 0;
}

.edit-list-tray-conflict-value-label {
    color: var(--p-text-muted-color);
}
</style>
