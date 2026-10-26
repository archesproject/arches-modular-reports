<script setup lang="ts">
import { computed, shallowRef } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";

import { loadComponent } from "@/arches_modular_reports/ModularReport/utils.ts";
import { useReportData } from "@/arches_modular_reports/ResourceReport/composables/useReportData.ts";
import { localizeLabel } from "@/arches_modular_reports/ResourceReport/utils/localize-label.ts";

import type {
    ComponentNode,
    DrawerConfig,
    LabelledConfig,
} from "@/arches_modular_reports/ResourceReport/types.ts";

const { component } = defineProps<{
    component: ComponentNode<DrawerConfig>;
}>();

const { $gettext } = useGettext();
const reportData = useReportData();

const openPanel = shallowRef<ComponentNode<LabelledConfig> | null>(null);

const bodyNodes = computed(() => component.config.components ?? []);

const triggers = computed(() =>
    (component.config.panels ?? [])
        .filter(
            (panel) =>
                panel.config.requires_edit !== true || reportData.value.canEdit,
        )
        .map((panel) => ({ panel, label: panelLabel(panel) })),
);

const resourceLabel = computed(
    () =>
        reportData.value.resource.name?.trim() ||
        reportData.value.context.graph.name,
);

function panelLabel(panel: ComponentNode<LabelledConfig>): string {
    return localizeLabel(
        panel.config.label ?? null,
        reportData.value.context.language,
    );
}

function togglePanel(panel: ComponentNode<LabelledConfig>): void {
    if (openPanel.value === panel) {
        openPanel.value = null;
        return;
    }
    openPanel.value = panel;
}

function closeDrawer(): void {
    openPanel.value = null;
}
</script>

<template>
    <div class="report-drawer">
        <div
            v-if="triggers.length > 0"
            class="report-drawer-triggers"
        >
            <Button
                v-for="trigger in triggers"
                :key="trigger.label"
                variant="outlined"
                severity="secondary"
                size="small"
                :rounded="true"
                :icon="trigger.panel.config.icon ?? undefined"
                :label="trigger.label"
                :aria-pressed="openPanel === trigger.panel"
                @click="togglePanel(trigger.panel)"
            />
        </div>
        <div class="report-drawer-stage">
            <div class="report-drawer-content">
                <component
                    :is="loadComponent(bodyNode.component)"
                    v-for="(bodyNode, bodyIndex) in bodyNodes"
                    :key="bodyIndex"
                    :component="bodyNode"
                />
            </div>
            <Transition name="report-drawer-fade">
                <div
                    v-if="openPanel"
                    class="report-drawer-scrim"
                    @click="closeDrawer"
                />
            </Transition>
            <Transition name="report-drawer-slide">
                <section
                    v-if="openPanel"
                    class="report-drawer-panel"
                    :aria-label="panelLabel(openPanel)"
                >
                    <header class="report-drawer-header">
                        <div class="report-drawer-crumb">
                            <span class="report-drawer-crumb-root">{{
                                resourceLabel
                            }}</span>
                            <i
                                class="pi pi-angle-right"
                                aria-hidden="true"
                            />
                            <span class="report-drawer-crumb-leaf">{{
                                panelLabel(openPanel)
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
                    <div class="report-drawer-body">
                        <component
                            :is="loadComponent(openPanel.component)"
                            :component="openPanel"
                        />
                    </div>
                </section>
            </Transition>
        </div>
    </div>
</template>

<style scoped>
.report-drawer {
    display: flex;
    flex: 1;
    flex-direction: column;
    min-block-size: 0;
}

.report-drawer-triggers {
    display: flex;
    flex-wrap: wrap;
    gap: 0.8rem;
    padding: 1.6rem;
    border-block-end: 0.1rem solid var(--p-content-border-color);
}

.report-drawer-stage {
    position: relative;
    flex: 1;
    min-block-size: 0;
    overflow: hidden;
}

.report-drawer-content {
    display: flex;
    flex-direction: column;
    gap: 1.6rem;
    block-size: 100%;
    padding: 1.6rem;
    overflow: auto;
}

.report-drawer-scrim {
    position: absolute;
    inset: 0;
    background: var(--p-mask-background);
}

.report-drawer-panel {
    position: absolute;
    inset-block: 0;
    inset-inline-end: 0;
    display: flex;
    flex-direction: column;
    inline-size: 90%;
    background: var(--p-content-background);
    border-inline-start: 0.1rem solid var(--p-content-border-color);
}

.report-drawer-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 1.2rem;
    padding-block: 1.4rem 1rem;
    padding-inline: 1.6rem;
    border-block-end: 0.1rem solid var(--p-content-border-color);
    background: var(--p-content-hover-background);
}

.report-drawer-crumb {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.5rem;
    font-size: 1.3rem;
}

.report-drawer-crumb-root {
    color: var(--p-text-muted-color);
}

.report-drawer-crumb-leaf {
    font-weight: 700;
}

.report-drawer-body {
    flex: 1;
    min-block-size: 0;
    overflow: auto;
}

.report-drawer-fade-enter-active,
.report-drawer-fade-leave-active {
    transition: opacity 0.2s ease;
}

.report-drawer-fade-enter-from,
.report-drawer-fade-leave-to {
    opacity: 0;
}

.report-drawer-slide-enter-active,
.report-drawer-slide-leave-active {
    transition: transform 0.24s ease;
}

.report-drawer-slide-enter-from,
.report-drawer-slide-leave-to {
    transform: translateX(100%);
}

.report-drawer-slide-enter-from:dir(rtl),
.report-drawer-slide-leave-to:dir(rtl) {
    transform: translateX(-100%);
}
</style>
