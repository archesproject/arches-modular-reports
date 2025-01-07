<script setup lang="ts">
import { onMounted, ref, watch } from "vue";

import {
    fetchCardFromNodegroupId,
    fetchNodegroupTileData,
} from "@/arches_provenance/EditableReport/api.ts";
import { ASC, ROWS_PER_PAGE_OPTIONS } from "@/arches_provenance/constants.ts";
import DataTable from "@/arches_provenance/EditableReport/components/DataTable.vue";

import type { ColumnDatum } from "@/arches_provenance/EditableReport/types";

const props = defineProps<{
    component: {
        config: {
            nodegroup_id: string;
            nodes: string[];
        };
    };
    resourceInstanceId: string;
}>();

const queryTimeoutValue = 500;
let timeout: ReturnType<typeof setTimeout> | null = null;

const rowsPerPage = ref(ROWS_PER_PAGE_OPTIONS[0]);
const currentPage = ref(1);
const query = ref("");
const sortField = ref("");
const direction = ref(ASC);
const paginatorKey = ref(0);
const currentlyDisplayedTableData = ref<unknown[]>([]);
const searchResultsTotalCount = ref(0);
const isLoading = ref(false);
const hasLoadingError = ref(false);
const columnData = ref<ColumnDatum[]>([]);
const cardinality = ref("");

const pageNumberToNodegroupTileData = ref<Record<number, unknown[]>>({});

watch(query, () => {
    if (timeout) {
        clearTimeout(timeout);
    }

    timeout = setTimeout(() => {
        pageNumberToNodegroupTileData.value = {};
        paginatorKey.value += 1;
        fetchData(1);
    }, queryTimeoutValue);
});

watch([direction, sortField, rowsPerPage], () => {
    pageNumberToNodegroupTileData.value = {};
    paginatorKey.value += 1;
    fetchData(1);
});

watch(currentPage, () => {
    if (currentPage.value in pageNumberToNodegroupTileData.value) {
        currentlyDisplayedTableData.value =
            pageNumberToNodegroupTileData.value[currentPage.value];
    } else {
        fetchData(currentPage.value);
    }
});

function getDisplayValue(
    tileData: Record<string, string | Record<string, unknown>>,
    key: string,
): string | null {
    const queue: Array<Record<string, unknown>> = [tileData];

    while (queue.length > 0) {
        const currentItem = queue.shift();

        if (Object.prototype.hasOwnProperty.call(currentItem, key)) {
            const value = currentItem![key];

            if ("@display_value" in (value as Record<string, unknown>)) {
                return (value as Record<string, string>)["@display_value"];
            }
        }

        for (const val of Object.values(currentItem!)) {
            if (val && typeof val === "object") {
                queue.push(val as Record<string, unknown>);
            }
        }
    }

    return null;
}

function deriveColumnData(
    config: { nodes: string[] },
    cardData: {
        nodes: { alias: string; nodeid: string }[];
        widgets: { node_id: string; label: string }[];
    },
): ColumnDatum[] {
    return config.nodes!.map((nodeAlias: string) => {
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
            nodeAlias: nodeAlias,
            widgetLabel: matchingWidget?.label || "",
        };
    });
}

async function fetchData(page: number = 1) {
    isLoading.value = true;

    try {
        const {
            results,
            page: fetchedPage,
            total_count: totalCount,
        } = await fetchNodegroupTileData(
            props.resourceInstanceId,
            props.component.config.nodegroup_id,
            rowsPerPage.value,
            page,
            sortField.value,
            direction.value,
            query.value,
        );

        pageNumberToNodegroupTileData.value[fetchedPage] = results;
        currentlyDisplayedTableData.value = results;
        currentPage.value = fetchedPage;
        searchResultsTotalCount.value = totalCount;
    } catch (error) {
        hasLoadingError.value = true;
        throw error;
    } finally {
        isLoading.value = false;
    }
}

onMounted(() => {
    fetchData();
    fetchCardFromNodegroupId(props.component.config.nodegroup_id).then(
        (fetchedCardData) => {
            columnData.value = deriveColumnData(
                props.component.config,
                fetchedCardData,
            );

            cardinality.value = fetchedCardData.cardinality;
        },
    );
});
</script>

<template>
    <DataTable
        v-model:rows-per-page="rowsPerPage"
        v-model:current-page="currentPage"
        v-model:query="query"
        v-model:sort-field="sortField"
        v-model:direction="direction"
        :is-empty="!isLoading && !query && !timeout && !searchResultsTotalCount"
        :is-loading
        :has-loading-error
        mode="data"
        :config="props.component.config"
        :paginator-key
        :get-display-value
        :currently-displayed-table-data
        :search-results-total-count
        :column-data
        :sortable="cardinality === 'n'"
    />
</template>
