<script setup lang="ts">
import DataTable from "@/arches_provenance/EditableReport/components/DataTable.vue";

defineProps<{
    component: {
        config: {
            nodegroup_id: string;
            nodes: string[];
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
