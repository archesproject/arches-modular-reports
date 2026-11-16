<script setup lang="ts">
const { name } = defineProps<{
    name: string;
}>();
</script>

<!-- Names the language of a value not in the reader's own. -->
<template>
    <span class="language-name">{{ name }}</span>
</template>

<style scoped>
.language-name {
    flex-shrink: 0;
    padding-block: 0.1rem;
    padding-inline: 0.7rem;
    border: 0.1rem solid var(--resource-report-bar-border-color);
    border-radius: 1rem;
    background: var(--resource-report-muted-background);
    color: var(--p-text-muted-color);
    font-size: 1.1rem;
    font-weight: 600;
    line-height: 1.4;
    white-space: nowrap;
}
</style>
