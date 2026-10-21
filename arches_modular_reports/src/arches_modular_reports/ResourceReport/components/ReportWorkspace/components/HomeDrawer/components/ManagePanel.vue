<script setup lang="ts">
import { computed, ref } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";
import ConfirmDialog from "openvue/confirmdialog";
import Message from "openvue/message";
import { useConfirm } from "openvue/useconfirm";

import {
    copyResource,
    deleteResource,
    resourceReportUrl,
    searchUrl,
} from "@/arches_modular_reports/ResourceReport/api.ts";
import { toError } from "@/arches_modular_reports/utils.ts";

import type { ReportData } from "@/arches_modular_reports/ResourceReport/types.ts";

const CONFIRM_GROUP = "manage-panel";

const { reportData } = defineProps<{
    reportData: ReportData;
    panelConfig: Record<string, unknown>;
}>();

const { $gettext } = useGettext();
const confirm = useConfirm();

const copiedResourceId = ref<string | null>(null);
const isCopying = ref(false);
const isDeleting = ref(false);
const actionError = ref<Error | null>(null);

const permissions = computed(() => reportData.context.permissions);
const lifecycleState = computed(() => reportData.context.lifecycle_state);

async function createCopy(): Promise<void> {
    isCopying.value = true;
    actionError.value = null;
    try {
        copiedResourceId.value = await copyResource(
            reportData.resource.resourceinstanceid,
        );
    } catch (error) {
        actionError.value = toError(error);
    } finally {
        isCopying.value = false;
    }
}

function confirmDelete(): void {
    let message = $gettext("Deleting this resource cannot be undone.");
    if (reportData.changeSet.pendingChanges.value.length > 0) {
        message = $gettext(
            "Deleting this resource cannot be undone, and your pending edits will be discarded.",
        );
    }
    confirm.require({
        group: CONFIRM_GROUP,
        header: $gettext("Delete this resource?"),
        message,
        acceptLabel: $gettext("Delete Resource"),
        rejectLabel: $gettext("Cancel"),
        acceptProps: { severity: "danger" },
        accept: deleteThisResource,
    });
}

async function deleteThisResource(): Promise<void> {
    isDeleting.value = true;
    actionError.value = null;
    try {
        await deleteResource(reportData.resource.resourceinstanceid);
        reportData.changeSet.discardAll();
        window.location.assign(searchUrl());
    } catch (error) {
        actionError.value = toError(error);
    } finally {
        isDeleting.value = false;
    }
}

function printReport(): void {
    window.print();
}
</script>

<template>
    <div class="manage">
        <ConfirmDialog :group="CONFIRM_GROUP" />
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
        <section
            v-if="permissions.can_copy"
            class="manage-card"
        >
            <h4 class="manage-card-title">{{ $gettext("Copy Resource") }}</h4>
            <Button
                v-if="copiedResourceId === null"
                icon="pi pi-copy"
                size="small"
                :label="$gettext('Create Copy')"
                :loading="isCopying"
                @click="createCopy"
            />
            <template v-else>
                <Message
                    severity="success"
                    variant="simple"
                    icon="pi pi-check-circle"
                >
                    <span>{{ $gettext("Copy created.") }}</span>
                </Message>
                <Button
                    as="a"
                    variant="outlined"
                    size="small"
                    :href="resourceReportUrl(copiedResourceId)"
                    :label="$gettext('Open Copy')"
                />
            </template>
        </section>
        <section
            v-if="permissions.can_delete"
            class="manage-card"
        >
            <h4 class="manage-card-title">{{ $gettext("Delete") }}</h4>
            <p class="manage-status">
                <span>{{ $gettext("Current status:") }}</span>
                <strong>{{ lifecycleState.name }}</strong>
            </p>
            <template v-if="lifecycleState.can_delete_resource_instances">
                <Message
                    severity="warn"
                    variant="simple"
                    icon="pi pi-exclamation-triangle"
                >
                    <span>
                        {{
                            $gettext("Deleting this resource cannot be undone.")
                        }}
                    </span>
                </Message>
                <Button
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
                class="manage-note"
            >
                {{
                    $gettext(
                        "This resource can't be deleted in its current lifecycle state.",
                    )
                }}
            </p>
        </section>
        <section class="manage-card">
            <h4 class="manage-card-title">{{ $gettext("Print") }}</h4>
            <Button
                icon="pi pi-print"
                variant="outlined"
                size="small"
                :label="$gettext('Print')"
                @click="printReport"
            />
        </section>
    </div>
</template>

<style scoped>
.manage {
    display: flex;
    flex-direction: column;
    gap: 1.6rem;
    padding: 1.6rem;
}

.manage-card {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 0.8rem;
    padding: 1.6rem;
    border: 0.1rem solid var(--p-content-border-color);
    border-radius: var(--p-content-border-radius);
    background: var(--p-content-background);
}

.manage-card-title {
    margin: 0;
    font-size: 1.4rem;
    font-weight: 700;
}

.manage-status {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin: 0;
}

.manage-note {
    margin: 0;
    color: var(--p-text-muted-color);
}
</style>
