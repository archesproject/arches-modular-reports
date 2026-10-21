<script setup lang="ts">
import { computed, shallowRef } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";

import EditHistoryPanel from "@/arches_modular_reports/ResourceReport/components/ReportWorkspace/components/HomeDrawer/components/EditHistoryPanel.vue";
import ImagesPanel from "@/arches_modular_reports/ResourceReport/components/ReportWorkspace/components/HomeDrawer/components/ImagesPanel.vue";
import ManagePanel from "@/arches_modular_reports/ResourceReport/components/ReportWorkspace/components/HomeDrawer/components/ManagePanel.vue";
import RelatedResourcesPanel from "@/arches_modular_reports/ResourceReport/components/ReportWorkspace/components/HomeDrawer/components/RelatedResourcesPanel.vue";

import { loadComponent } from "@/arches_modular_reports/ModularReport/utils.ts";
import { localizeLabel } from "@/arches_modular_reports/ResourceReport/utils/localize-label.ts";

import type { Component } from "vue";
import type {
    DrawerPanelConfig,
    ReportData,
} from "@/arches_modular_reports/ResourceReport/types.ts";

const EDIT_HISTORY_PANEL = "EditHistoryPanel";
const DRAWER_PANEL_COMPONENTS: Record<string, Component> = {
    EditHistoryPanel,
    ImagesPanel,
    ManagePanel,
    RelatedResourcesPanel,
};

const { entries, reportData } = defineProps<{
    entries: DrawerPanelConfig[];
    reportData: ReportData;
}>();

const { $gettext } = useGettext();

const openEntry = shallowRef<DrawerPanelConfig | null>(null);

const triggers = computed(() =>
    entries
        .filter(
            (entry) =>
                entry.component !== EDIT_HISTORY_PANEL ||
                reportData.context.permissions.can_edit,
        )
        .map((entry) => ({ entry, label: entryLabel(entry) })),
);

const resourceLabel = computed(
    () => reportData.resource.name?.trim() || reportData.context.graph.name,
);

const openPanelComponent = computed(() => {
    if (openEntry.value === null) {
        return undefined;
    }
    return (
        DRAWER_PANEL_COMPONENTS[openEntry.value.component] ??
        loadComponent(openEntry.value.component)
    );
});

function entryLabel(entry: DrawerPanelConfig): string {
    return localizeLabel(entry.label, reportData.context.language);
}

function toggleEntry(entry: DrawerPanelConfig): void {
    if (openEntry.value === entry) {
        openEntry.value = null;
        return;
    }
    openEntry.value = entry;
}

function closeDrawer(): void {
    openEntry.value = null;
}
</script>

<template>
    <div class="home-drawer">
        <div
            v-if="triggers.length > 0"
            class="home-drawer-triggers"
        >
            <Button
                v-for="trigger in triggers"
                :key="trigger.label"
                variant="outlined"
                severity="secondary"
                size="small"
                :rounded="true"
                :icon="trigger.entry.icon"
                :label="trigger.label"
                :aria-pressed="openEntry === trigger.entry"
                @click="toggleEntry(trigger.entry)"
            />
        </div>
        <div class="home-drawer-stage">
            <div class="home-drawer-content">
                <slot />
            </div>
            <Transition name="home-drawer-fade">
                <div
                    v-if="openEntry"
                    class="home-drawer-scrim"
                    @click="closeDrawer"
                />
            </Transition>
            <Transition name="home-drawer-slide">
                <section
                    v-if="openEntry"
                    class="home-drawer-panel"
                    :aria-label="entryLabel(openEntry)"
                >
                    <header class="home-drawer-header">
                        <div class="home-drawer-crumb">
                            <span class="home-drawer-crumb-root">{{
                                resourceLabel
                            }}</span>
                            <i
                                class="pi pi-angle-right"
                                aria-hidden="true"
                            />
                            <span class="home-drawer-crumb-leaf">{{
                                entryLabel(openEntry)
                            }}</span>
                        </div>
                        <Button
                            icon="pi pi-times"
                            variant="text"
                            severity="secondary"
                            size="small"
                            :rounded="true"
                            :aria-label="$gettext('Close')"
                            @click="closeDrawer"
                        />
                    </header>
                    <div class="home-drawer-body">
                        <component
                            :is="openPanelComponent"
                            :report-data="reportData"
                            :panel-config="openEntry.config"
                        />
                    </div>
                </section>
            </Transition>
        </div>
    </div>
</template>

<style scoped>
.home-drawer {
    display: flex;
    flex: 1;
    flex-direction: column;
    min-block-size: 0;
}

.home-drawer-triggers {
    display: flex;
    flex-wrap: wrap;
    gap: 0.8rem;
    padding: 1.6rem;
    border-block-end: 0.1rem solid var(--p-content-border-color);
}

.home-drawer-stage {
    position: relative;
    flex: 1;
    min-block-size: 0;
    overflow: hidden;
}

.home-drawer-content {
    block-size: 100%;
    overflow: auto;
}

.home-drawer-scrim {
    position: absolute;
    inset: 0;
    background: var(--p-mask-background);
}

.home-drawer-panel {
    position: absolute;
    inset-block: 0;
    inset-inline-end: 0;
    display: flex;
    flex-direction: column;
    inline-size: 90%;
    background: var(--p-content-background);
    border-inline-start: 0.1rem solid var(--p-content-border-color);
}

.home-drawer-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 1.2rem;
    padding-block: 1.4rem 1rem;
    padding-inline: 1.6rem;
    border-block-end: 0.1rem solid var(--p-content-border-color);
    background: var(--p-content-hover-background);
}

.home-drawer-crumb {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.5rem;
    font-size: 1.3rem;
}

.home-drawer-crumb-root {
    color: var(--p-text-muted-color);
}

.home-drawer-crumb-leaf {
    font-weight: 700;
}

.home-drawer-body {
    flex: 1;
    min-block-size: 0;
    overflow: auto;
}

.home-drawer-fade-enter-active,
.home-drawer-fade-leave-active {
    transition: opacity 0.2s ease;
}

.home-drawer-fade-enter-from,
.home-drawer-fade-leave-to {
    opacity: 0;
}

.home-drawer-slide-enter-active,
.home-drawer-slide-leave-active {
    transition: transform 0.24s ease;
}

.home-drawer-slide-enter-from,
.home-drawer-slide-leave-to {
    transform: translateX(100%);
}

.home-drawer-slide-enter-from:dir(rtl),
.home-drawer-slide-leave-to:dir(rtl) {
    transform: translateX(-100%);
}
</style>
