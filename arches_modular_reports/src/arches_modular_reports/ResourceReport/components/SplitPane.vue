<script setup lang="ts">
import { computed } from "vue";

import Splitter from "openvue/splitter";
import SplitterPanel from "openvue/splitterpanel";

import { loadComponent } from "@/arches_modular_reports/ModularReport/utils.ts";

import type {
    ComponentNode,
    SplitPaneConfig,
} from "@/arches_modular_reports/ResourceReport/types.ts";

const SPLITTER_STATE_KEY_PREFIX = "arches-modular-reports-split-pane";
const MINIMUM_PANE_SIZE = 20;
const MAIN_PANE_SIZE = 60;
const ASIDE_PANE_SIZE = 40;
const FULL_PANE_SIZE = 100;

const { component } = defineProps<{
    component: ComponentNode<SplitPaneConfig>;
}>();

const mainNodes = computed(() => component.config.main ?? []);

const asideNodes = computed(() => component.config.aside ?? []);

const hasAside = computed(() => asideNodes.value.length > 0);

const mainPaneSize = computed(() => {
    if (hasAside.value) {
        return MAIN_PANE_SIZE;
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
    return `${SPLITTER_STATE_KEY_PREFIX}:${regionPaths.join(",")}`;
});
</script>

<template>
    <Splitter
        :key="String(hasAside)"
        class="split-pane"
        state-storage="local"
        :state-key="splitterStateKey"
    >
        <SplitterPanel
            class="split-pane-region"
            :size="mainPaneSize"
            :min-size="MINIMUM_PANE_SIZE"
        >
            <component
                :is="loadComponent(childNode.component)"
                v-for="(childNode, childIndex) in mainNodes"
                :key="childIndex"
                :component="childNode"
            />
        </SplitterPanel>
        <SplitterPanel
            v-if="hasAside"
            class="split-pane-region split-pane-aside"
            :size="ASIDE_PANE_SIZE"
            :min-size="MINIMUM_PANE_SIZE"
        >
            <component
                :is="loadComponent(childNode.component)"
                v-for="(childNode, childIndex) in asideNodes"
                :key="childIndex"
                :component="childNode"
            />
        </SplitterPanel>
    </Splitter>
</template>

<style scoped>
.split-pane {
    flex: 1;
    min-block-size: 0;
    border: none;
    border-radius: 0;
}

.split-pane-region {
    position: relative;
    display: flex;
    flex-direction: column;
    min-inline-size: 0;
    overflow: auto;
}

.split-pane-aside {
    background: var(--p-resource-report-aside-background);
}

@media (prefers-reduced-motion: no-preference) {
    .split-pane-region {
        scroll-behavior: smooth;
    }
}
</style>
