<script setup lang="ts">
const { config } = defineProps<{
    config: { graph_id: string };
    resourceInstanceId: string;
}>();
</script>

<template>
    <div>
        {{ config.graph_id }}
    </div>
</template>
