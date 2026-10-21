<script setup lang="ts">
import { computed } from "vue";

import { highlightSegments } from "@/arches_modular_reports/ResourceReport/utils/highlight-segments.ts";

const { text, query } = defineProps<{
    text: string;
    query: string;
}>();

const segments = computed(() => highlightSegments(text, query));
</script>

<template>
    <template
        v-for="(segment, segmentIndex) in segments"
        :key="segmentIndex"
    >
        <mark
            v-if="segment.matched"
            class="highlighted-text-match"
        >
            {{ segment.text }}
        </mark>
        <span v-else>{{ segment.text }}</span>
    </template>
</template>

<style scoped>
.highlighted-text-match {
    background: var(--p-highlight-background);
    color: var(--p-highlight-color);
}
</style>
