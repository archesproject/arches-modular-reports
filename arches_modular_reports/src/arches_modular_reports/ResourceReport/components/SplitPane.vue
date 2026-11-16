<script setup lang="ts">
import { computed, onBeforeUnmount, ref, useTemplateRef, watch } from "vue";

import Splitter from "openvue/splitter";
import SplitterPanel from "openvue/splitterpanel";

import { loadComponent } from "@/arches_modular_reports/ModularReport/utils.ts";
import { useReportData } from "@/arches_modular_reports/ResourceReport/composables/useReportData.ts";
import { useWorkspaceHeaderHost } from "@/arches_modular_reports/ResourceReport/composables/useWorkspaceHeaderHost.ts";
import { provideWorkspaceOverlayHost } from "@/arches_modular_reports/ResourceReport/composables/useWorkspaceOverlayHost.ts";

import type {
    ComponentNode,
    SplitPaneConfig,
} from "@/arches_modular_reports/ResourceReport/types.ts";

const SPLITTER_STATE_KEY_PREFIX = "arches-modular-reports-split-pane";
const MINIMUM_PANE_SIZE = 20;
const DEFAULT_ASIDE_PANE_SIZE = 40;
const EDITING_ASIDE_PANE_SIZE = 60;
const EDITOR_PANEL_COMPONENT_NAME = "EditorPanel";
const FULL_PANE_SIZE = 100;

const { component } = defineProps<{
    component: ComponentNode<SplitPaneConfig>;
}>();

const reportData = useReportData();

const mainHeader = useTemplateRef<HTMLElement>("mainHeader");
useWorkspaceHeaderHost(mainHeader);

const overlayHost = useTemplateRef<HTMLElement>("overlayHost");
provideWorkspaceOverlayHost(overlayHost);

const mainHeaderBlockSize = ref(0);

const mainNodes = computed(() => component.config.main ?? []);

const asideNodes = computed(() => component.config.aside ?? []);

const asideFooterNodes = computed(() => component.config.aside_footer ?? []);

const hasAside = computed(
    () => asideNodes.value.length > 0 || asideFooterNodes.value.length > 0,
);

const configuredAsidePaneSize = computed(
    () => component.config.aside_size ?? DEFAULT_ASIDE_PANE_SIZE,
);

const isEditingInAside = computed(
    () =>
        reportData.value.editor.target !== null &&
        asideNodes.value.some(
            (childNode) =>
                childNode.component.split("/").at(-1) ===
                EDITOR_PANEL_COMPONENT_NAME,
        ),
);

// The editor needs room for its form, so the aside widens while it is open
// and goes back to its own size when it closes.
const asidePaneSize = computed(() => {
    if (isEditingInAside.value) {
        return Math.max(configuredAsidePaneSize.value, EDITING_ASIDE_PANE_SIZE);
    }
    return configuredAsidePaneSize.value;
});

const mainPaneSize = computed(() => {
    if (hasAside.value) {
        return FULL_PANE_SIZE - asidePaneSize.value;
    }
    return FULL_PANE_SIZE;
});

const splitterStateKey = computed(() => {
    if (!hasAside.value) {
        return undefined;
    }
    const regionPaths = [...mainNodes.value, ...asideNodes.value].map(
        (childNode) => childNode.component,
    );
    // The size is part of the key, so a changed configured size replaces a
    // remembered split rather than being masked by it, and the split while
    // editing is remembered apart from the one while not.
    return `${SPLITTER_STATE_KEY_PREFIX}:${regionPaths.join(",")}:${asidePaneSize.value}`;
});

// Sticky elements further down the main region (e.g. the report sub-tabs)
// offset themselves by the pinned header's height via this custom property.
const mainRegionStyle = computed(() => ({
    "--split-pane-main-header-block-size": `${mainHeaderBlockSize.value}rem`,
}));

let headerResizeObserver: ResizeObserver | null = null;

watch(
    mainHeader,
    (headerElement) => {
        headerResizeObserver?.disconnect();
        headerResizeObserver = null;
        if (headerElement === null) {
            return;
        }
        headerResizeObserver = new ResizeObserver(([entry]) => {
            mainHeaderBlockSize.value = toRem(entry.borderBoxSize[0].blockSize);
        });
        headerResizeObserver.observe(headerElement);
    },
    { flush: "post" },
);

onBeforeUnmount(() => {
    headerResizeObserver?.disconnect();
});

// ResizeObserver reports CSS pixels; express them relative to the root font size.
function toRem(pixels: number): number {
    const rootFontSize = parseFloat(
        getComputedStyle(document.documentElement).fontSize,
    );
    return pixels / rootFontSize;
}
</script>

<template>
    <div class="split-pane">
        <Splitter
            :key="String(hasAside)"
            class="split-pane-splitter"
            state-storage="local"
            :state-key="splitterStateKey"
        >
            <SplitterPanel
                class="split-pane-region"
                :style="mainRegionStyle"
                :size="mainPaneSize"
                :min-size="MINIMUM_PANE_SIZE"
            >
                <div
                    ref="mainHeader"
                    class="split-pane-main-header"
                ></div>
                <component
                    :is="loadComponent(childNode.component)"
                    v-for="(childNode, childIndex) in mainNodes"
                    :key="childIndex"
                    :component="childNode"
                />
            </SplitterPanel>
            <SplitterPanel
                v-if="hasAside"
                class="split-pane-aside"
                :size="asidePaneSize"
                :min-size="MINIMUM_PANE_SIZE"
            >
                <div class="split-pane-region split-pane-aside-stage">
                    <component
                        :is="loadComponent(childNode.component)"
                        v-for="(childNode, childIndex) in asideNodes"
                        :key="childIndex"
                        :component="childNode"
                    />
                </div>
                <div
                    v-if="asideFooterNodes.length > 0"
                    class="split-pane-aside-footer"
                >
                    <component
                        :is="loadComponent(childNode.component)"
                        v-for="(childNode, childIndex) in asideFooterNodes"
                        :key="childIndex"
                        :component="childNode"
                    />
                </div>
            </SplitterPanel>
        </Splitter>
        <div
            ref="overlayHost"
            class="split-pane-overlay-host"
        ></div>
    </div>
</template>

<style scoped>
.split-pane {
    position: relative;
    display: flex;
    flex: 1;
    min-block-size: 0;
}

.split-pane-splitter {
    flex: 1;
    min-inline-size: 0;
    border: none;
    border-radius: 0;
}

/* Empty until a panel teleports in; it must never take clicks itself. It sits
   above the pinned main header, so a full-width panel covers it too. */
.split-pane-overlay-host {
    position: absolute;
    inset: 0;
    z-index: 3;
    pointer-events: none;
}

.split-pane :deep(.p-splitter-gutter) {
    border-inline-start: 0.1rem solid var(--p-content-border-color);
    background: var(--resource-report-panel-background);
}

.split-pane :deep(.p-splitter-gutter-handle) {
    background: transparent;
}

.split-pane :deep(.p-splitter-gutter:hover .p-splitter-gutter-handle),
.split-pane :deep(.p-splitter-gutter-handle:focus-visible) {
    background: var(--p-content-border-color);
}

.split-pane-region {
    position: relative;
    display: flex;
    flex-direction: column;
    min-inline-size: 0;
    overflow: auto;
}

.split-pane-main-header {
    position: sticky;
    inset-block-start: 0;
    z-index: 2;
    flex-shrink: 0;
    background: var(--p-content-background);
}

.split-pane-aside {
    display: flex;
    flex-direction: column;
    min-inline-size: 0;
    background: var(--resource-report-panel-background);
}

.split-pane-aside-stage {
    flex: 1;
    min-block-size: 0;
}

/* At most half the aside, so a long edit list can't crowd out the panels
   above it; the footer's content scrolls within that. */
.split-pane-aside-footer {
    display: flex;
    flex-direction: column;
    flex-shrink: 0;
    max-block-size: 50%;
}

@media (prefers-reduced-motion: no-preference) {
    .split-pane-region {
        scroll-behavior: smooth;
    }
}
</style>
