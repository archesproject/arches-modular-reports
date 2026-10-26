<script setup lang="ts">
import { computed } from "vue";

import { loadComponent } from "@/arches_modular_reports/ModularReport/utils.ts";

import type {
    ComponentNode,
    StackConfig,
} from "@/arches_modular_reports/ResourceReport/types.ts";

const { component } = defineProps<{
    component: ComponentNode<StackConfig>;
}>();

const childNodes = computed(() => component.config.components ?? []);
</script>

<template>
    <div class="report-stack">
        <component
            :is="loadComponent(childNode.component)"
            v-for="(childNode, childIndex) in childNodes"
            :key="childIndex"
            :component="childNode"
        />
    </div>
</template>

<style scoped>
.report-stack {
    display: flex;
    flex-direction: column;
    gap: 0.8rem;
}
</style>
