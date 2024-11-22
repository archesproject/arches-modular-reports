<script setup lang="ts">
import { ref, onMounted } from "vue";
import {
    fetchNodegroup,
    fetchNodegroupTileData,
} from "@/arches_provenance/EditableReport/api.ts";

const props = defineProps<{
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    component: Record<string, any>;
    resourceInstanceId: string;
}>();

const nodeGroupData = ref(null);
const nodeGroupTileData = ref(null);

onMounted(() => {
    fetchNodegroup(props.component.config?.nodegroup_id).then((data) => {
        nodeGroupData.value = data;
    });

    fetchNodegroupTileData(
        props.resourceInstanceId,
        props.component.config?.nodegroup_id,
    ).then((data) => {
        nodeGroupTileData.value = data;
    });
});
</script>

<template>
    <pre>{{ nodeGroupData }}</pre>
    <pre>{{ nodeGroupTileData }}</pre>
</template>
