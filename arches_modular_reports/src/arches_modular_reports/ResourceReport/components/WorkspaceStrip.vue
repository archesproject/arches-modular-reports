<script setup lang="ts">
import Tab from "openvue/tab";
import TabList from "openvue/tablist";
import Tabs from "openvue/tabs";

import type { ResolvedWorkspace } from "@/arches_modular_reports/ResourceReport/types.ts";

const SELECT_WORKSPACE = "select-workspace" as const;

const { workspaces, activeWorkspaceId } = defineProps<{
    workspaces: ResolvedWorkspace[];
    activeWorkspaceId: string;
}>();

const emit = defineEmits<{
    (event: typeof SELECT_WORKSPACE, workspaceId: string): void;
}>();

function onTabChange(workspaceId: string | number): void {
    emit(SELECT_WORKSPACE, String(workspaceId));
}
</script>

<template>
    <Tabs
        class="workspace-strip"
        :value="activeWorkspaceId"
        @update:value="onTabChange"
    >
        <TabList>
            <Tab
                v-for="workspace in workspaces"
                :key="workspace.id"
                :value="workspace.id"
            >
                <span>{{ workspace.label }}</span>
            </Tab>
        </TabList>
    </Tabs>
</template>

<style scoped>
.workspace-strip :deep(.p-tablist-tab-list) {
    background: var(
        --p-resource-report-strip-background,
        var(--p-content-hover-background)
    );
}

.workspace-strip :deep(.p-tab) {
    padding-block: 0.9rem;
    padding-inline: 1.6rem;
    color: var(--p-text-muted-color);
    font-size: 1.3rem;
    font-weight: 500;
    letter-spacing: 0.08rem;
    text-transform: uppercase;
}

.workspace-strip :deep(.p-tab-active) {
    color: var(--p-primary-color);
}
</style>
