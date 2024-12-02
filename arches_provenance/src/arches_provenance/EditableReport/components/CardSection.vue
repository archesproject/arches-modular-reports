<script setup lang="ts">
const { config } = defineProps<{
    config: { nodes: string[]; nodegroup_id: string };
    resourceInstanceId?: string;
}>();
</script>

<template>
    <div
        v-for="node in config.nodes"
        :key="node"
    >
        {{ node }}
    </div>
</template>
