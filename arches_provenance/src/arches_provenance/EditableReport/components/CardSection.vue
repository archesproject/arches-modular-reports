<script setup lang="ts">
import { ref, onMounted, watch } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "primevue/button";
import Column from "primevue/column";
import DataTable from "primevue/datatable";
import Select from "primevue/select";

import {
    fetchCardFromNodegroupId,
    fetchNodegroupTileData,
} from "@/arches_provenance/EditableReport/api.ts";

import type { Ref } from "vue";

const { $gettext } = useGettext();

const props = defineProps<{
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    component: Record<string, any>;
    resourceInstanceId: string;
}>();

interface ColumnName {
    node_name: string;
    widget_label: string;
}

const isLoading = ref(false);
// const isLoadingAdditionalResults = ref(false);
const searchResultsPage = ref(1);
const searchResultsTotalCount = ref(0);
const query = ref("");

const tableTitle = ref("");
const columnNames: Ref<ColumnName[]> = ref([]);

const cardData = ref(null);
const nodegroupTileData = ref([]);

const rowsPerPageOptions = ref([5, 10, 20]);
const rowsPerPage = ref(5);

watch(rowsPerPage, (newValue) => {
    foo(
        props.resourceInstanceId,
        props.component.config?.nodegroup_id,
        newValue,
    );
});

onMounted(() => {
    foo(
        props.resourceInstanceId,
        props.component.config?.nodegroup_id,
        rowsPerPage.value,
    );

    fetchCardFromNodegroupId(props.component.config?.nodegroup_id).then(
        (fetchedCardData) => {
            tableTitle.value = fetchedCardData?.name;
            columnNames.value = deriveColumnNames(
                props.component.config,
                fetchedCardData,
            );

            cardData.value = fetchedCardData;
        },
    );
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

function foo(resourceInstanceId, nodegroupId, rowsPerPage) {
    isLoading.value = true;

    fetchNodegroupTileData(resourceInstanceId, nodegroupId, rowsPerPage).then(
        (fetchedNodegroupTileData) => {
            nodegroupTileData.value = fetchedNodegroupTileData["results"];
            searchResultsPage.value = fetchedNodegroupTileData["page"];
            searchResultsTotalCount.value =
                fetchedNodegroupTileData["total_count"];

            isLoading.value = false;
        },
    );
}

function bar(event, callback) {
    console.log("bar");
    callback(event);
}
</script>

<template>
    <DataTable
        v-if="nodegroupTileData.length > 0"
        paginator
        lazy
        :value="nodegroupTileData"
        :loading="isLoading"
        :total-records="searchResultsTotalCount"
        :rows="rowsPerPage"
    >
        <template #header>
            <h4 style="color: var(--p-content-color)">{{ tableTitle }}</h4>

            <div>
                <span>{{ $gettext("Number of rows:") }}</span>
                <Select
                    v-model="rowsPerPage"
                    :options="rowsPerPageOptions"
                />
            </div>
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

        <template
            #paginatorcontainer="{
                first,
                last,
                page,
                pageCount,
                prevPageCallback,
                nextPageCallback,
                totalRecords,
            }"
        >
            <div>
                <Button
                    icon="pi pi-chevron-left"
                    rounded
                    text
                    :disabled="page === 0"
                    @click="prevPageCallback"
                />
                <div>
                    <span
                        >Showing {{ first }} to {{ last }} of
                        {{ totalRecords }}</span
                    >
                    <span>Page {{ page + 1 }} of {{ pageCount }}</span>
                </div>
                <Button
                    icon="pi pi-chevron-right"
                    rounded
                    text
                    :disabled="page === pageCount - 1"
                    @click="
                        (e) => {
                            bar(e, nextPageCallback);
                        }
                    "
                />
            </div>
        </template>
    </DataTable>

    <!-- <pre>{{ columnNames }}</pre> -->
    <!-- <pre>{{ props.component.config }}</pre> -->
    <!-- <pre>{{ cardData }}</pre> -->
    <!-- <pre>{{ nodegroupTileData }}</pre> -->
</template>
