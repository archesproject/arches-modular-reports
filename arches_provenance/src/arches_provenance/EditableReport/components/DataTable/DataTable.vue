<script setup lang="ts">
import { ref, onMounted, watch } from "vue";
import { useGettext } from "vue3-gettext";

import Column from "primevue/column";
import DataTable from "primevue/datatable";
import IconField from "primevue/iconfield";
import InputIcon from "primevue/inputicon";
import InputText from "primevue/inputtext";
import Paginator from "primevue/paginator";
import Select from "primevue/select";

import { useToast } from "primevue/usetoast";

import { DEFAULT_ERROR_TOAST_LIFE } from "@/arches_provenance/constants.ts";

import {
    fetchCardFromNodegroupId,
    fetchNodegroupTileData,
} from "@/arches_provenance/EditableReport/api.ts";

import type { PageState } from "primevue/paginator";

const { $gettext } = useGettext();
const toast = useToast();

interface ColumnDatum {
    nodeAlias: string;
    widgetLabel: string;
}

interface CardData {
    name: string;
    nodes: { alias: string; nodeid: string }[];
    widgets: { node_id: string; label: string }[];
}

const props = defineProps<{
    component: {
        config: {
            nodegroup_id: string;
            nodes: string[];
        };
    };
    resourceInstanceId: string;
}>();

const ASC = "asc";
const DESC = "desc";
const ROWS_PER_PAGE_OPTIONS = [5, 10, 20];

const queryTimeoutValue = 500;
let timeout: ReturnType<typeof setTimeout> | null = null;

const tableTitle = ref("");
const columnData = ref<ColumnDatum[]>([]);
const isLoading = ref(false);

const cardData = ref<CardData | null>(null);

const paginatorKey = ref(0);
const currentPage = ref(1);
const rowsPerPageOptions = ref(ROWS_PER_PAGE_OPTIONS);
const rowsPerPage = ref(ROWS_PER_PAGE_OPTIONS[0]);

const pageNumberToNodegroupTileData = ref<Record<number, unknown[]>>({});
const currentlyDisplayedTableData = ref<unknown[]>([]);
const searchResultsTotalCount = ref(0);

const sortNodeId = ref("");
const sortOrder = ref(ASC);

const query = ref("");

watch(
    [sortOrder, sortNodeId, rowsPerPage],
    ([newSortOrder, newSortNodeId, newRowsPerPage]) => {
        pageNumberToNodegroupTileData.value = {};
        paginatorKey.value += 1;

        fetchData(
            props.resourceInstanceId,
            props.component.config.nodegroup_id,
            newRowsPerPage,
            1, // Reset to first page
            newSortNodeId,
            newSortOrder,
            query.value,
        );
    },
);

watch(query, (newQuery) => {
    if (timeout) {
        clearTimeout(timeout);
    }

    timeout = setTimeout(() => {
        pageNumberToNodegroupTileData.value = {};

        fetchData(
            props.resourceInstanceId,
            props.component.config.nodegroup_id,
            rowsPerPage.value,
            1, // Reset to first page
            sortNodeId.value,
            sortOrder.value,
            newQuery,
        );
    }, queryTimeoutValue);
});

onMounted(() => {
    fetchCardFromNodegroupId(props.component.config?.nodegroup_id).then(
        (fetchedCardData) => {
            tableTitle.value = fetchedCardData?.name;
            columnData.value = deriveColumnData(
                props.component.config,
                fetchedCardData,
            );

            cardData.value = fetchedCardData;
        },
    );

    fetchData(
        props.resourceInstanceId,
        props.component.config?.nodegroup_id,
        rowsPerPage.value,
        currentPage.value,
        sortNodeId.value,
        sortOrder.value,
        query.value,
    );
});

async function fetchData(
    resourceInstanceId: string,
    nodegroupId: string,
    rowsPerPage: number,
    page: number,
    sortNodeId: string,
    sortOrder: string,
    query: string,
) {
    isLoading.value = true;

    try {
        const {
            results,
            page: fetchedPage,
            total_count: totalCount,
        } = await fetchNodegroupTileData(
            resourceInstanceId,
            nodegroupId,
            rowsPerPage,
            page,
            sortNodeId,
            sortOrder,
            query,
        );

        pageNumberToNodegroupTileData.value[fetchedPage] = results;
        currentlyDisplayedTableData.value = results;
        currentPage.value = fetchedPage;
        searchResultsTotalCount.value = totalCount;
    } catch (error) {
        toast.add({
            severity: "error",
            life: DEFAULT_ERROR_TOAST_LIFE,
            summary: $gettext("Unable to fetch resource"),
            detail: error instanceof Error ? error.message : String(error),
        });

        throw error;
    } finally {
        isLoading.value = false;
    }
}

function deriveColumnData(
    config: { nodes: string[] },
    cardData: {
        nodes: { alias: string; nodeid: string }[];
        widgets: { node_id: string; label: string }[];
    },
): ColumnDatum[] {
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
            nodeAlias: nodeAlias,
            widgetLabel: matchingWidget?.label || "",
        };
    });
}

function getDisplayValue(
    tileData: Record<string, unknown>,
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

function onUpdatePagination(event: PageState) {
    const page = event.page + 1; // PrimeVue paginator is 0-indexed

    if (pageNumberToNodegroupTileData.value[page]) {
        currentlyDisplayedTableData.value =
            pageNumberToNodegroupTileData.value[page];
        currentPage.value = page;
    } else {
        fetchData(
            props.resourceInstanceId,
            props.component.config?.nodegroup_id,
            rowsPerPage.value,
            page,
            sortNodeId.value,
            sortOrder.value,
            query.value,
        );
    }
}

function onUpdateSortField(event: string) {
    const selectedNode = cardData.value?.nodes.find(
        (node) => node.alias === event,
    );

    sortNodeId.value = selectedNode!.nodeid;
}

function onUpdateSortOrder(event: number | undefined) {
    if (event === 1) {
        sortOrder.value = ASC;
    } else if (event === -1) {
        sortOrder.value = DESC;
    }
}
</script>

<template>
    <DataTable
        :value="currentlyDisplayedTableData"
        :loading="isLoading"
        :total-records="searchResultsTotalCount"
        @update:sort-field="onUpdateSortField"
        @update:sort-order="onUpdateSortOrder"
    >
        <template #header>
            <h4 style="color: var(--p-content-color)">{{ tableTitle }}</h4>

            <div style="display: flex; justify-content: space-between">
                <div>
                    <span>{{ $gettext("Number of rows:") }}</span>
                    <Select
                        v-model="rowsPerPage"
                        style="margin: 0 1rem"
                        :options="rowsPerPageOptions"
                    />
                </div>

                <IconField>
                    <InputIcon
                        class="pi pi-search"
                        aria-hidden="true"
                    />
                    <InputText
                        v-model="query"
                        style="height: 100%"
                        :placeholder="$gettext('Search')"
                        :aria-label="$gettext('Search')"
                    />
                </IconField>
            </div>
        </template>

        <Column
            field=""
            header=""
        />
        <Column
            v-for="columnDatum of columnData"
            :key="columnDatum.nodeAlias"
            :field="columnDatum.nodeAlias"
            :header="columnDatum.widgetLabel"
            sortable
        >
            <template #body="slotProps">
                {{ getDisplayValue(slotProps.data, slotProps.field) }}
            </template>
        </Column>
    </DataTable>

    <Paginator
        v-if="searchResultsTotalCount > rowsPerPage"
        :key="paginatorKey"
        :rows="rowsPerPage"
        :total-records="searchResultsTotalCount"
        @page="onUpdatePagination"
    />
</template>

<style scoped>
:deep(.p-paginator) {
    border-radius: 0;
}

:deep(.p-datatable-column-sorted) {
    background: var(--p-datatable-header-cell-background);
}
</style>
