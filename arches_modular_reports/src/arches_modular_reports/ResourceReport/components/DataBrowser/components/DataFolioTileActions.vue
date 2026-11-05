<script setup lang="ts">
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";

const EDIT = "edit" as const;
const DELETE = "delete" as const;
const UNDO_DELETE = "undo-delete" as const;

const { label, isMarkedForDeletion, isBusy } = defineProps<{
    label: string;
    isMarkedForDeletion: boolean;
    isBusy: boolean;
}>();

const emit = defineEmits<{
    (event: typeof EDIT): void;
    (event: typeof DELETE): void;
    (event: typeof UNDO_DELETE): void;
}>();

const { $gettext } = useGettext();
</script>

<template>
    <div class="data-folio-tile-actions">
        <Button
            v-if="isMarkedForDeletion"
            class="data-folio-action"
            variant="outlined"
            size="small"
            :label="$gettext('Undo delete')"
            :aria-label="
                $gettext(
                    'Undo deleting %{entry}',
                    {
                        entry: label,
                    },
                    true,
                )
            "
            :disabled="isBusy"
            @click="emit(UNDO_DELETE)"
        />
        <template v-else>
            <Button
                class="data-folio-action"
                variant="outlined"
                size="small"
                :label="$gettext('Edit')"
                :aria-label="
                    $gettext(
                        'Edit %{entry}',
                        {
                            entry: label,
                        },
                        true,
                    )
                "
                @click="emit(EDIT)"
            />
            <Button
                class="data-folio-action data-folio-action-danger"
                variant="outlined"
                size="small"
                severity="danger"
                :label="$gettext('Delete')"
                :aria-label="
                    $gettext(
                        'Delete %{entry}',
                        {
                            entry: label,
                        },
                        true,
                    )
                "
                :disabled="isBusy"
                @click="emit(DELETE)"
            />
        </template>
    </div>
</template>

<style scoped>
.data-folio-tile-actions {
    display: flex;
    gap: 0.3rem;
}

.data-folio-tile-actions .data-folio-action {
    --p-button-label-font-weight: 600;
    min-block-size: 2.4rem;
    padding-block: 0.1rem;
    padding-inline: 0.6rem;
    border-color: var(--resource-report-bar-border-color);
    border-radius: 0.3rem;
    background: var(--resource-report-row-entry-background);
    color: var(--p-text-muted-color);
    font-size: 1.1rem;
}

.data-folio-tile-actions .data-folio-action:not(:disabled):hover {
    border-color: var(--p-text-muted-color);
    background: var(--resource-report-bar-border-color);
    color: var(--p-text-color);
}

.data-folio-tile-actions .data-folio-action-danger,
.data-folio-tile-actions .data-folio-action-danger:not(:disabled):hover {
    border-color: var(--resource-report-deleted-color);
    background: var(--resource-report-deleted-background);
    color: var(--resource-report-deleted-color);
}

.data-folio-tile-actions .data-folio-action:disabled {
    opacity: 0.35;
}
</style>
