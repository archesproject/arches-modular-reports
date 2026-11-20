<script setup lang="ts">
import { computed, ref, shallowRef, watch } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";

import { loadComponent } from "@/arches_modular_reports/ModularReport/utils.ts";
import { useReportData } from "@/arches_modular_reports/ResourceReport/composables/useReportData.ts";
import { useWorkspaceOverlayHost } from "@/arches_modular_reports/ResourceReport/composables/useWorkspaceOverlayHost.ts";
import { localizeLabel } from "@/arches_modular_reports/ResourceReport/utils/localize-label.ts";

import type {
    ComponentNode,
    DrawerConfig,
    DrawerPanelCount,
    LabelledConfig,
} from "@/arches_modular_reports/ResourceReport/types.ts";

const { component } = defineProps<{
    component: ComponentNode<DrawerConfig>;
}>();

const { $gettext } = useGettext();
const reportData = useReportData();
const overlayHost = useWorkspaceOverlayHost();

const openPanel = shallowRef<ComponentNode<LabelledConfig> | null>(null);
const isExpanded = ref(false);
const savedChangesCount = ref(0);
const panelCounts = shallowRef(
    new Map<ComponentNode<LabelledConfig>, DrawerPanelCount>(),
);

const bodyNodes = computed(() => component.config.components ?? []);

const visiblePanels = computed(() =>
    (component.config.panels ?? []).filter(
        (panel) =>
            panel.config.requires_edit !== true || reportData.value.canEdit,
    ),
);

const triggers = computed(() =>
    visiblePanels.value.map((panel) => ({
        panel,
        label: panelLabel(panel),
        countLabel: countLabel(panel),
    })),
);

const resourceLabel = computed(
    () =>
        reportData.value.resource.name?.trim() ||
        reportData.value.context.graph.name,
);

const openPanelLabel = computed(() => {
    if (openPanel.value === null) {
        return "";
    }
    return panelLabel(openPanel.value);
});

const canExpand = computed(() => overlayHost.value !== null);

const isPanelExpanded = computed(() => isExpanded.value && canExpand.value);

const expandIcon = computed(() =>
    isPanelExpanded.value ? "pi pi-window-minimize" : "pi pi-window-maximize",
);

watch(
    () => reportData.value.changeSet.isSaving.value,
    (isSaving, wasSaving) => {
        if (
            wasSaving &&
            !isSaving &&
            reportData.value.changeSet.saveError.value === null
        ) {
            savedChangesCount.value += 1;
        }
    },
);

function panelLabel(panel: ComponentNode<LabelledConfig>): string {
    return localizeLabel(
        panel.config.label ?? null,
        reportData.value.context.language,
        reportData.value.context.default_language,
    );
}

function countLabel(panel: ComponentNode<LabelledConfig>): string | undefined {
    const panelCount = panelCounts.value.get(panel);
    if (panelCount === undefined) {
        return undefined;
    }
    if (panelCount.hasMore) {
        return $gettext("%{count}+", { count: String(panelCount.count) });
    }
    return String(panelCount.count);
}

function setPanelCount(
    panel: ComponentNode<LabelledConfig>,
    panelCount: DrawerPanelCount,
): void {
    panelCounts.value = new Map(panelCounts.value).set(panel, panelCount);
}

function togglePanel(panel: ComponentNode<LabelledConfig>): void {
    if (openPanel.value === panel) {
        closeDrawer();
        return;
    }
    openPanel.value = panel;
}

function toggleExpanded(): void {
    isExpanded.value = !isExpanded.value;
}

function closeDrawer(): void {
    openPanel.value = null;
    isExpanded.value = false;
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
                badge-severity="secondary"
                :rounded="true"
                :icon="trigger.panel.config.icon ?? undefined"
                :label="trigger.label"
                :badge="trigger.countLabel"
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
            <Teleport
                :to="overlayHost ?? 'body'"
                :disabled="!isPanelExpanded"
            >
                <Transition name="report-drawer-fade">
                    <div
                        v-if="openPanel"
                        class="report-drawer-scrim"
                        @click="closeDrawer"
                    />
                </Transition>
                <Transition name="report-drawer-slide">
                    <section
                        v-show="openPanel"
                        class="report-drawer-panel"
                        :class="{
                            'report-drawer-panel-expanded': isPanelExpanded,
                        }"
                        :aria-label="openPanelLabel"
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
                                    openPanelLabel
                                }}</span>
                            </div>
                            <div class="report-drawer-header-actions">
                                <Button
                                    v-if="canExpand"
                                    variant="text"
                                    severity="secondary"
                                    size="small"
                                    :icon="expandIcon"
                                    :rounded="true"
                                    :aria-label="$gettext('Expand panel')"
                                    :aria-pressed="isPanelExpanded"
                                    :title="$gettext('Expand panel')"
                                    @click="toggleExpanded"
                                />
                                <Button
                                    icon="pi pi-times"
                                    variant="text"
                                    severity="secondary"
                                    size="small"
                                    :rounded="true"
                                    :aria-label="$gettext('Close')"
                                    @click="closeDrawer"
                                />
                            </div>
                        </header>
                        <div class="report-drawer-body">
                            <div
                                v-for="(panel, panelIndex) in visiblePanels"
                                v-show="panel === openPanel"
                                :key="`${panelIndex}:${savedChangesCount}`"
                            >
                                <component
                                    :is="loadComponent(panel.component)"
                                    :component="panel"
                                    @count="setPanelCount(panel, $event)"
                                />
                            </div>
                        </div>
                    </section>
                </Transition>
            </Teleport>
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
    align-content: center;
    align-items: center;
    gap: 0.8rem;
    min-block-size: var(--resource-report-bar-block-size);
    padding-block: 0.2rem;
    padding-inline: 1.5rem;
    border-block-end: 0.1rem solid var(--p-content-border-color);
    background: var(--resource-report-muted-background);
}

.report-drawer-triggers > .p-button {
    --p-button-label-font-weight: 600;
    gap: 0.6rem;
    block-size: 2.7rem;
    padding-block: 0;
    padding-inline: 1.2rem;
    border-color: var(--p-content-border-color);
    background: var(--p-content-background);
    color: var(--p-text-muted-color);
    font-size: 1.2rem;
    line-height: 1.2;
}

.report-drawer-triggers > .p-button:not(:disabled):hover {
    border-color: var(--p-primary-color);
    background: var(--p-content-background);
    color: var(--p-primary-color);
}

.report-drawer-triggers > .p-button :deep(.p-badge) {
    min-inline-size: 1.8rem;
    block-size: 1.8rem;
    font-size: 1.1rem;
    line-height: 1.8rem;
}

.report-drawer-triggers > .p-button[aria-pressed="true"],
.report-drawer-triggers > .p-button[aria-pressed="true"]:not(:disabled):hover {
    border-color: var(--resource-report-drawer-trigger-open-background);
    background: var(--resource-report-drawer-trigger-open-background);
    color: var(--resource-report-drawer-trigger-open-color);
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
    gap: 1.2rem;
    block-size: 100%;
    padding: 2rem;
    overflow: auto;
}

.report-drawer-scrim {
    position: absolute;
    inset: 0;
    background: color-mix(in srgb, var(--p-surface-950) 28%, transparent);
    pointer-events: auto;
}

.report-drawer-panel {
    position: absolute;
    inset-block: 0;
    inset-inline-end: 0;
    display: flex;
    flex-direction: column;
    inline-size: 90%;
    background: var(--resource-report-panel-background);
    border-inline-start: 0.1rem solid var(--resource-report-bar-border-color);
    pointer-events: auto;
}

.report-drawer-panel-expanded {
    inline-size: 100%;
    border-inline-start: none;
}

.report-drawer-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 1.2rem;
    padding-block: 1.4rem 1rem;
    padding-inline: 1.6rem;
    border-block-end: 0.1rem solid var(--p-content-border-color);
    background: var(--resource-report-drawer-header-background);
}

.report-drawer-header-actions {
    display: flex;
    flex-shrink: 0;
    gap: 0.4rem;
}

.report-drawer-header-actions > .p-button {
    flex-shrink: 0;
    inline-size: 2.8rem;
    block-size: 2.8rem;
    padding: 0;
    border: none;
}

.report-drawer-header-actions > .p-button[aria-pressed="true"] {
    background: var(--resource-report-bar-background);
    color: var(--p-text-color);
}

.report-drawer-header-actions > .p-button:not(:disabled):hover {
    background: var(--resource-report-bar-background);
    color: var(--p-text-color);
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
    font-weight: 500;
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
