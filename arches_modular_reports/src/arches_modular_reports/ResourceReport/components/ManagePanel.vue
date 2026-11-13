<script setup lang="ts">
import { computed, ref, watchEffect } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";
import Dialog from "openvue/dialog";
import InputText from "openvue/inputtext";
import Message from "openvue/message";

import {
    copyResource,
    deleteResource,
    fetchResourceCopies,
} from "@/arches_modular_reports/ResourceReport/api.ts";
import { useReportData } from "@/arches_modular_reports/ResourceReport/composables/useReportData.ts";

import type {
    ComponentNode,
    LabelledConfig,
    ResourceCopy,
} from "@/arches_modular_reports/ResourceReport/types.ts";

defineProps<{
    component: ComponentNode<LabelledConfig>;
}>();

const { $gettext } = useGettext();
const reportData = useReportData();

const copies = ref<ResourceCopy[]>([]);
const nextCursor = ref<string | null>(null);
const isLoadingCopies = ref(false);
const copiesError = ref<Error | null>(null);
const copyName = ref("");
const isCopying = ref(false);
const isConfirmingDelete = ref(false);
const isDeleting = ref(false);
const deleteError = ref<Error | null>(null);
const actionError = ref<Error | null>(null);

const permissions = computed(() => reportData.value.context.permissions);
const lifecycleState = computed(() => reportData.value.context.lifecycle_state);
const resourceInstanceId = computed(
    () => reportData.value.resource.resourceinstanceid,
);
const deleteWarning = computed(() => {
    if (reportData.value.changeSet.pendingChanges.value.length > 0) {
        return $gettext(
            "Deleting this resource cannot be undone, and your pending edits will be discarded.",
        );
    }
    return $gettext("Deleting this resource cannot be undone.");
});

watchEffect(() => {
    loadCopies(resourceInstanceId.value, null);
});

async function loadCopies(
    resourceId: string,
    cursor: string | null,
): Promise<void> {
    isLoadingCopies.value = true;
    copiesError.value = null;
    try {
        const copiesPage = await fetchResourceCopies(resourceId, cursor);
        if (cursor === null) {
            copies.value = copiesPage.results;
            copyName.value = copiesPage.default_name;
        } else {
            copies.value = [...copies.value, ...copiesPage.results];
        }
        nextCursor.value = copiesPage.next_cursor;
    } catch (error) {
        copiesError.value = error as Error;
    } finally {
        isLoadingCopies.value = false;
    }
}

function loadMoreCopies(): void {
    loadCopies(resourceInstanceId.value, nextCursor.value);
}

async function createCopy(): Promise<void> {
    isCopying.value = true;
    actionError.value = null;
    try {
        await copyResource(resourceInstanceId.value, copyName.value.trim());
        await loadCopies(resourceInstanceId.value, null);
    } catch (error) {
        actionError.value = error as Error;
    } finally {
        isCopying.value = false;
    }
}

function formatTimestamp(timestamp: string): string {
    return new Date(timestamp).toLocaleString(
        reportData.value.context.language,
    );
}

function confirmDelete(): void {
    deleteError.value = null;
    isConfirmingDelete.value = true;
}

// The dialog stays open until the server answers, so a slow delete shows
// progress and a failed one shows its error where the user is looking.
async function deleteThisResource(): Promise<void> {
    isDeleting.value = true;
    deleteError.value = null;
    try {
        await deleteResource(
            reportData.value.context.graph.slug,
            resourceInstanceId.value,
        );
        reportData.value.markDeleted();
        isConfirmingDelete.value = false;
    } catch (error) {
        deleteError.value = error as Error;
    } finally {
        isDeleting.value = false;
    }
}
</script>

<template>
    <div class="manage">
        <Dialog
            v-model:visible="isConfirmingDelete"
            modal
            :draggable="false"
            :closable="!isDeleting"
            :close-on-escape="!isDeleting"
            :header="$gettext('Delete this resource?')"
            :pt="{
                root: {
                    class: 'manage-confirm-dialog',
                    role: 'alertdialog',
                    style: {
                        width: '40rem',
                        maxWidth: 'calc(100vw - 3.2rem)',
                        borderRadius: '0.15rem',
                    },
                },
                header: {
                    style: {
                        background: 'var(--p-content-hover-background)',
                        color: 'var(--p-text-color)',
                        borderBottom:
                            '0.1rem solid var(--p-content-border-color)',
                        borderRadius: '0.15rem 0.15rem 0 0',
                    },
                },
            }"
        >
            <Message
                v-if="deleteError"
                class="manage-confirm-note"
                severity="error"
                size="small"
                icon="pi pi-times-circle"
            >
                {{
                    $gettext(
                        "Unable to delete this resource: %{message}",
                        { message: deleteError.message },
                        true,
                    )
                }}
            </Message>
            <Message
                v-else-if="isDeleting"
                class="manage-confirm-note"
                severity="info"
                size="small"
                icon="pi pi-spin pi-spinner"
            >
                {{ $gettext("Deleting this resource…") }}
            </Message>
            <Message
                v-else
                class="manage-confirm-note"
                severity="warn"
                size="small"
                icon="pi pi-exclamation-triangle"
            >
                {{ deleteWarning }}
            </Message>
            <template #footer>
                <Button
                    :label="$gettext('Cancel')"
                    :disabled="isDeleting"
                    autofocus
                    @click="isConfirmingDelete = false"
                />
                <Button
                    severity="danger"
                    :label="$gettext('Delete Resource')"
                    :loading="isDeleting"
                    @click="deleteThisResource"
                />
            </template>
        </Dialog>
        <Message
            v-if="actionError"
            severity="error"
        >
            <span>
                {{
                    $gettext(
                        "Unable to complete this action: %{message}",
                        { message: actionError.message },
                        true,
                    )
                }}
            </span>
        </Message>
        <section class="manage-section">
            <h4 class="manage-section-label">
                <i
                    class="pi pi-copy"
                    aria-hidden="true"
                />
                <span>{{ $gettext("Manage Copies") }}</span>
            </h4>
            <form
                v-if="permissions.can_copy"
                class="manage-copy-form"
                @submit.prevent="createCopy"
            >
                <label
                    for="manage-copy-name"
                    class="manage-field-label"
                >
                    {{ $gettext("Name of the copy") }}
                </label>
                <InputText
                    id="manage-copy-name"
                    v-model="copyName"
                    class="manage-copy-name"
                    required
                />
                <Button
                    type="submit"
                    icon="pi pi-copy"
                    size="small"
                    :label="$gettext('Create Copy')"
                    :loading="isCopying"
                    :disabled="copyName.trim() === ''"
                />
            </form>
            <Message
                v-if="copiesError"
                severity="error"
            >
                <span>
                    {{
                        $gettext(
                            "Unable to load the copies: %{message}",
                            { message: copiesError.message },
                            true,
                        )
                    }}
                </span>
            </Message>
            <p
                v-else-if="!isLoadingCopies && copies.length === 0"
                class="manage-empty"
            >
                {{ $gettext("No copies of this resource yet.") }}
            </p>
            <ul
                v-if="copies.length > 0"
                class="manage-copies"
            >
                <li
                    v-for="resourceCopy in copies"
                    :key="resourceCopy.editlogid"
                    class="manage-copy"
                >
                    <Button
                        v-if="resourceCopy.report_url !== null"
                        as="a"
                        variant="link"
                        size="small"
                        class="manage-copy-link"
                        :href="resourceCopy.report_url"
                        :label="resourceCopy.name"
                    />
                    <span
                        v-else
                        class="manage-copy-deleted"
                    >
                        <s>{{ resourceCopy.name }}</s>
                        <span>{{ $gettext("(deleted)") }}</span>
                    </span>
                    <span class="manage-copy-meta">
                        <span class="manage-copy-user">
                            <i
                                class="pi pi-user"
                                aria-hidden="true"
                            />
                            <span>{{ resourceCopy.user }}</span>
                        </span>
                        <time :datetime="resourceCopy.timestamp">
                            {{ formatTimestamp(resourceCopy.timestamp) }}
                        </time>
                    </span>
                </li>
            </ul>
            <Button
                v-if="nextCursor !== null"
                class="manage-load-more"
                variant="link"
                size="small"
                :label="$gettext('Load more')"
                :loading="isLoadingCopies"
                @click="loadMoreCopies"
            />
        </section>
        <section
            v-if="permissions.can_delete"
            class="manage-section"
        >
            <h4 class="manage-section-label">
                <i
                    class="pi pi-trash"
                    aria-hidden="true"
                />
                <span>{{ $gettext("Delete Resource") }}</span>
            </h4>
            <p class="manage-status">
                <span>{{ $gettext("Current status:") }}</span>
                <strong>{{ lifecycleState.name }}</strong>
            </p>
            <template v-if="lifecycleState.can_delete_resource_instances">
                <Message
                    class="manage-note-message"
                    severity="warn"
                    size="small"
                    icon="pi pi-exclamation-triangle"
                >
                    {{ deleteWarning }}
                </Message>
                <Button
                    class="manage-delete"
                    icon="pi pi-trash"
                    severity="danger"
                    size="small"
                    :label="$gettext('Delete Resource')"
                    :loading="isDeleting"
                    @click="confirmDelete"
                />
            </template>
            <p
                v-else
                class="manage-empty"
            >
                {{
                    $gettext(
                        "This resource can't be deleted in its current lifecycle state.",
                    )
                }}
            </p>
        </section>
    </div>
</template>

<style scoped>
.manage {
    display: flex;
    flex-direction: column;
    gap: 2.6rem;
    padding: 1.6rem;
}

.manage-section {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 0.8rem;
}

.manage-section-label {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin: 0;
    color: var(--p-text-muted-color);
    font-size: 1.2rem;
    font-weight: 700;
    letter-spacing: 0.08rem;
    text-transform: uppercase;
}

.manage-copy-form {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
    inline-size: 100%;
}

/* Matches the report editor panel's field labels. */
.manage-field-label {
    color: var(--p-text-muted-color);
    font-size: 1.25rem;
    font-weight: 600;
}

.manage-copy-name {
    inline-size: 100%;
    margin-block-end: 0.3rem;
    border-radius: 0.15rem;
}

.manage-section :deep(.p-button:not(.p-button-link)) {
    border-radius: 0.15rem;
}

.manage-empty {
    margin: 0;
    color: var(--p-text-muted-color);
    font-style: italic;
}

.manage-copies {
    display: flex;
    flex-direction: column;
    inline-size: 100%;
    margin: 0;
    padding: 0;
    list-style: none;
}

.manage-copy {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 0.2rem;
    padding-block: 0.6rem;
    border-block-end: 0.1rem solid var(--p-content-border-color);
}

.manage-copy-link {
    padding: 0;
    text-align: start;
}

.manage-copy-deleted {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    color: var(--p-text-muted-color);
}

.manage-copy-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem 1.2rem;
    color: var(--p-text-muted-color);
    font-size: 1.2rem;
}

.manage-copy-user {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
}

.manage-load-more {
    padding-inline: 0;
}

.manage-status {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin: 0;
}

/* Matches the warning in the delete confirmation dialog. */
.manage-note-message {
    inline-size: 100%;
    border-radius: 0.15rem;
}

.manage-note-message :deep(.p-message-content) {
    gap: 1.5rem;
}

.manage-note-message :deep(.p-message-text) {
    font-size: 1.25rem;
    line-height: 1.4;
}

.manage-note-message :deep(.p-message-icon) {
    font-size: 1.4rem;
}
</style>

<!-- Not scoped: the dialog is teleported to <body>, outside this component. -->
<style>
.manage-confirm-dialog .p-dialog-content {
    padding-block-start: 1.25rem;
}

.manage-confirm-dialog .manage-confirm-note {
    inline-size: 100%;
    border-radius: 0.15rem;
}

.manage-confirm-dialog .manage-confirm-note .p-message-content {
    gap: 1.5rem;
}

/* The small Message sizes its own text and icon; match the create dialog. */
.manage-confirm-dialog .manage-confirm-note .p-message-text {
    font-size: 1.25rem;
    line-height: 1.4;
}

.manage-confirm-dialog .manage-confirm-note .p-message-icon {
    font-size: 1.4rem;
}

.manage-confirm-dialog .p-dialog-footer .p-button {
    border-radius: 0.15rem;
}
</style>
