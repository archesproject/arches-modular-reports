<script setup lang="ts">
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";

const { label, isMarkedForDeletion, isBusy } = defineProps<{
    label: string;
    isMarkedForDeletion: boolean;
    isBusy: boolean;
}>();

const emit = defineEmits<{
    (event: "edit"): void;
    (event: "delete"): void;
    (event: "undo-delete"): void;
}>();

const { $gettext } = useGettext();
</script>

<template>
    <div class="data-folio-tile-actions">
        <Button
            v-if="isMarkedForDeletion"
            icon="pi pi-undo"
            variant="text"
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
            @click="emit('undo-delete')"
        />
        <template v-else>
            <Button
                icon="pi pi-pencil"
                variant="text"
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
                @click="emit('edit')"
            />
            <Button
                icon="pi pi-trash"
                variant="text"
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
                @click="emit('delete')"
            />
        </template>
    </div>
</template>

<style scoped>
.data-folio-tile-actions {
    display: flex;
    gap: 0.2rem;
}
</style>
