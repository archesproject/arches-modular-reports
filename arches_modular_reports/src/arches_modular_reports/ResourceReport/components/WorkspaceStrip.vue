<script setup lang="ts">
import Tab from "openvue/tab";
import TabList from "openvue/tablist";
import Tabs from "openvue/tabs";

import type { ResolvedWorkspace } from "@/arches_modular_reports/ResourceReport/types.ts";

const SELECT_WORKSPACE = "select-workspace" as const;
const WORKSPACE_STRIP_TOKENS = {
    tablist: { background: "{resource.report.strip.background}" },
    tab: { padding: "0.9rem 1.6rem", fontWeight: "500" },
};

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
        :show-navigators="false"
        :dt="WORKSPACE_STRIP_TOKENS"
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
.workspace-strip :deep(.p-tab) {
    font-size: 1.3rem;
    letter-spacing: 0.08rem;
    text-transform: uppercase;
}
</style>
