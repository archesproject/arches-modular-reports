<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

import { fetchRelatedResourceData } from "@/arches_provenance/EditableReport/api.ts";
import { ASC, ROWS_PER_PAGE_OPTIONS } from "@/arches_provenance/constants.ts";
import DataTable from "@/arches_provenance/EditableReport/components/DataTable.vue";

const props = defineProps<{
    component: {
        config: {
            additional_nodes: string[];
            graph_id: string;
        };
    };
    resourceInstanceId: string;
}>();

const queryTimeoutValue = 500;
let timeout: ReturnType<typeof setTimeout> | null = null;

const rowsPerPage = ref(ROWS_PER_PAGE_OPTIONS[0]);
const currentPage = ref(1);
const query = ref("");
const sortField = ref("@relation_name");
const direction = ref(ASC);
const paginatorKey = ref(0);
const currentlyDisplayedTableData = ref<unknown[]>([]);
const searchResultsTotalCount = ref(0);
const isLoading = ref(false);
const hasLoadingError = ref(false);
const widgetLabelLookup = ref<Record<string, string>>({});

const pageNumberToNodegroupTileData = ref<Record<number, unknown[]>>({});

const columnData = computed(() => {
    return [
        {
            nodeAlias: "@relation_name",
            widgetLabel: "Relation Name",
        },
        {
            nodeAlias: "@display_name",
            widgetLabel: "Display Name",
        },
        ...props.component.config.additional_nodes.map((nodeAlias: string) => {
            return {
                nodeAlias,
                widgetLabel: widgetLabelLookup.value[nodeAlias] ?? nodeAlias,
            };
        }),
    ];
});

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

async function fetchData(page: number = 1) {
    isLoading.value = true;

    try {
        const {
            results,
            page: fetchedPage,
            total_count: totalCount,
            widget_labels: widgetLabels,
        } = await fetchRelatedResourceData(
            props.resourceInstanceId,
            props.component.config.graph_id,
            props.component.config.additional_nodes!,
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
        widgetLabelLookup.value = widgetLabels;
    } catch (error) {
        hasLoadingError.value = true;
        throw error;
    } finally {
        isLoading.value = false;
    }
}

onMounted(fetchData);
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
        mode="related-resources"
        :config="props.component.config"
        :paginator-key
        :currently-displayed-table-data
        :search-results-total-count
        :column-data
        :sortable="true"
    />
</template>
