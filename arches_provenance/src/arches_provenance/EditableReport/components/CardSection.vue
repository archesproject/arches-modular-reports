<script setup lang="ts">
import { ref, onMounted } from "vue";

import DataTable from "primevue/datatable";
import Column from "primevue/column";

import {
    fetchCardFromNodegroupId,
    fetchNodegroupTileData,
} from "@/arches_provenance/EditableReport/api.ts";

import type { Ref } from "vue";

const props = defineProps<{
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    component: Record<string, any>;
    resourceInstanceId: string;
}>();

interface ColumnName {
    node_name: string;
    widget_label: string;
}

const tableTitle = ref("");
const columnNames: Ref<ColumnName[]> = ref([]);

const cardData = ref(null);
const nodeGroupTileData = ref(null);

onMounted(() => {
    Promise.all([
        fetchCardFromNodegroupId(props.component.config?.nodegroup_id),
        fetchNodegroupTileData(
            props.resourceInstanceId,
            props.component.config?.nodegroup_id,
        ),
    ]).then(([fetchedCardData, fetchedNodeGroupTileData]) => {
        tableTitle.value = fetchedCardData?.name;
        columnNames.value = deriveColumnNames(
            props.component.config,
            fetchedCardData,
        );

        cardData.value = fetchedCardData;
        nodeGroupTileData.value = fetchedNodeGroupTileData;
    });
});

function deriveColumnNames(
    config: { nodes: string[] },
    cardData: {
        nodes: { alias: string; nodeid: string }[];
        widgets: { node_id: string; label: string }[];
    },
): ColumnName[] {
    return config.nodes.map((nodeAlias: string) => {
        const matchingNode = cardData.nodes.find(
            (node) => node.alias === nodeAlias,
        );

        let matchingWidget = null;
        if (matchingNode) {
            matchingWidget = cardData.widgets.find(
                (widget) => widget.node_id === matchingNode.nodeid,
            );
        }

        return {
            node_name: nodeAlias,
            widget_label: matchingWidget?.label || "",
        };
    });
}

function getDisplayValue(obj: Record<string, any>, key: string): string | null {
    if (obj[key] && obj[key]["@display_value"]) {
        return obj[key]["@display_value"];
    }

    for (const firstLevelKey in obj) {
        if (
            typeof obj[firstLevelKey] === "object" &&
            obj[firstLevelKey][key]?.["@display_value"]
        ) {
            return obj[firstLevelKey][key]["@display_value"];
        }
    }

    return null;
}
</script>

<template>
    <DataTable :value="nodeGroupTileData">
        <template #header>
            <h4>{{ tableTitle }}</h4>
        </template>
        <Column
            field=""
            header=""
        />
        <Column
            v-for="(col, index) of columnNames"
            :key="col.node_name + '_' + index"
            :field="col.node_name"
            :header="col.widget_label"
        >
            <template #body="slotProps">
                {{ getDisplayValue(slotProps.data, slotProps.field) }}
            </template>
        </Column>
    </DataTable>

    <!-- <pre>{{ columnNames }}</pre> -->
    <!-- <pre>{{ props.component.config }}</pre> -->
    <!-- <pre>{{ cardData }}</pre> -->
    <!-- <pre>{{ nodeGroupTileData }}</pre> -->
</template>
