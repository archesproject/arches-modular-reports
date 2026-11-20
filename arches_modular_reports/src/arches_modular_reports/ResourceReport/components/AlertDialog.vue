<script setup lang="ts">
import Button from "openvue/button";
import Dialog from "openvue/dialog";

import type { ButtonProps } from "openvue/button";

const CONFIRM_EVENT = "confirm" as const;

const DIALOG_PASSTHROUGH = {
    mask: {
        class: "alert-dialog-mask",
    },
    root: {
        class: "alert-dialog",
        role: "alertdialog",
        style: {
            inlineSize: "40rem",
            maxInlineSize: "100%",
            borderRadius: "0.15rem",
        },
    },
    header: {
        style: {
            background: "var(--p-content-hover-background)",
            color: "var(--p-text-color)",
            borderBlockEnd: "0.1rem solid var(--p-content-border-color)",
            borderRadius: "0.15rem 0.15rem 0 0",
        },
    },
};

const {
    header,
    cancelLabel,
    confirmLabel,
    confirmSeverity = "danger",
    isBusy = false,
} = defineProps<{
    header: string;
    cancelLabel: string;
    confirmLabel: string;
    confirmSeverity?: ButtonProps["severity"];
    isBusy?: boolean;
}>();

const emit = defineEmits<{
    (event: typeof CONFIRM_EVENT): void;
}>();

const isVisible = defineModel<boolean>("visible", { required: true });
</script>

<template>
    <Dialog
        v-model:visible="isVisible"
        :modal="true"
        :draggable="false"
        :closable="!isBusy"
        :close-on-escape="!isBusy"
        :header="header"
        :pt="DIALOG_PASSTHROUGH"
    >
        <slot />
        <template #footer>
            <Button
                :label="cancelLabel"
                :disabled="isBusy"
                :autofocus="true"
                @click="isVisible = false"
            />
            <Button
                :severity="confirmSeverity"
                :label="confirmLabel"
                :loading="isBusy"
                @click="emit(CONFIRM_EVENT)"
            />
        </template>
    </Dialog>
</template>

<style>
.alert-dialog-mask {
    padding-inline: 1.6rem;
}

.alert-dialog .p-dialog-content {
    padding-block-start: 1.25rem;
}

.alert-dialog .p-dialog-content .p-message {
    inline-size: 100%;
    border-radius: 0.15rem;
}

.alert-dialog .p-dialog-content .p-message-content {
    gap: 1.5rem;
}

.alert-dialog .p-dialog-content .p-message-text {
    font-size: 1.25rem;
    line-height: 1.4;
}

.alert-dialog .p-dialog-content .p-message-icon {
    font-size: 1.4rem;
}

.alert-dialog .p-dialog-footer .p-button {
    border-radius: 0.15rem;
}
</style>
