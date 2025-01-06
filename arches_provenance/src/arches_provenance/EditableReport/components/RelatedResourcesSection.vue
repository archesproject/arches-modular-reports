<script setup lang="ts">
import DataTable from "@/arches_provenance/EditableReport/components/DataTable.vue";

defineProps<{
    component: {
        config: {
            additional_nodes: string[];
            graph_id: string;
        };
    };
    resourceInstanceId: string;
}>();
</script>

<template>
    <DataTable
        :component
        :resource-instance-id
    />
</template>
