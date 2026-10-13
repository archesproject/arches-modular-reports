<script setup lang="ts">
import Tab from "openvue/tab";
import TabList from "openvue/tablist";
import Tabs from "openvue/tabs";

import type { ResolvedView } from "@/arches_modular_reports/ResourceReport/types.ts";

const SELECT_VIEW = "select-view" as const;

const { views, activeViewId } = defineProps<{
    views: ResolvedView[];
    activeViewId: string;
}>();

const emit = defineEmits<{
    (event: typeof SELECT_VIEW, viewId: string): void;
}>();

function onTabChange(viewId: string | number): void {
    emit(SELECT_VIEW, String(viewId));
}
</script>

<template>
    <Tabs
        class="view-strip"
        :value="activeViewId"
        @update:value="onTabChange"
    >
        <TabList>
            <Tab
                v-for="view in views"
                :key="view.id"
                :value="view.id"
            >
                <span>{{ view.label }}</span>
            </Tab>
        </TabList>
    </Tabs>
</template>

<style scoped>
.view-strip :deep(.p-tablist-tab-list) {
    background: var(
        --p-resource-report-strip-background,
        var(--p-content-hover-background)
    );
}

.view-strip :deep(.p-tab) {
    padding-block: 0.9rem;
    padding-inline: 1.6rem;
    color: var(--p-text-muted-color);
    font-size: 1.3rem;
    font-weight: 500;
    letter-spacing: 0.08rem;
    text-transform: uppercase;
}

.view-strip :deep(.p-tab-active) {
    color: var(--p-primary-color);
}
</style>
