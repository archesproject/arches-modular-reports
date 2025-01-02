<script setup lang="ts">
import { ref, onMounted, watch } from "vue";
import { useGettext } from "vue3-gettext";

import Column from "primevue/column";
import DataTable from "primevue/datatable";
import IconField from "primevue/iconfield";
import InputIcon from "primevue/inputicon";
import InputText from "primevue/inputtext";
import Message from "primevue/message";
import Paginator from "primevue/paginator";
import Select from "primevue/select";

import {
    fetchCardFromNodegroupId,
    fetchRelatedResourceData,
    fetchNodegroupTileData,
} from "@/arches_provenance/EditableReport/api.ts";
import HierarchicalTileViewer from "@/arches_provenance/EditableReport/components/HierarchicalTileViewer.vue";

import type { PageState } from "primevue/paginator";
import type { LabelBasedCard } from "@/arches_provenance/EditableReport/types";

const { $gettext } = useGettext();

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
            nodes?: string[];
            additional_nodes?: string[];
            graph_id?: string;
        };
    };
    resourceInstanceId: string;
}>();

const RELATED_RESOURCE_MODE = !!props.component.config.additional_nodes;
const ASC = "asc";
const DESC = "desc";
const CARDINALITY_N = "n";
const ROWS_PER_PAGE_OPTIONS = [5, 10, 20];

const queryTimeoutValue = 500;
let timeout: ReturnType<typeof setTimeout> | null = null;

const tableTitle = ref("");
const columnData = ref<ColumnDatum[]>([]);
const isLoading = ref(false);
const hasLoadingError = ref(false);

const cardData = ref<CardData | null>(null);
const cardinality = ref("");

const paginatorKey = ref(0);
const currentPage = ref(1);
const rowsPerPageOptions = ref(ROWS_PER_PAGE_OPTIONS);
const rowsPerPage = ref(ROWS_PER_PAGE_OPTIONS[0]);

const pageNumberToNodegroupTileData = ref<Record<number, unknown[]>>({});
const currentlyDisplayedTableData = ref<unknown[]>([]);
const searchResultsTotalCount = ref(0);
const widgetLabelLookup = ref<Record<string, string>>({});

const sortNodeId = ref(RELATED_RESOURCE_MODE ? "@relation_name" : "");
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
        paginatorKey.value += 1;

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

watch(widgetLabelLookup, () => {
    if (RELATED_RESOURCE_MODE) {
        columnData.value = deriveRelatedResourceColumnData(
            props.component.config,
        );
    }
});

onMounted(() => {
    if (!RELATED_RESOURCE_MODE) {
        fetchCardFromNodegroupId(props.component.config?.nodegroup_id).then(
            (fetchedCardData) => {
                tableTitle.value = fetchedCardData?.name;
                columnData.value = deriveColumnData(
                    props.component.config,
                    fetchedCardData,
                );

                cardinality.value = fetchedCardData.cardinality;
                cardData.value = fetchedCardData;
            },
        );
    }

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
        let promise;
        if (RELATED_RESOURCE_MODE) {
            promise = fetchRelatedResourceData(
                resourceInstanceId,
                props.component.config.graph_id!,
                props.component.config.additional_nodes!,
                rowsPerPage,
                page,
                sortNodeId,
                sortOrder,
            );
        } else {
            promise = fetchNodegroupTileData(
                resourceInstanceId,
                nodegroupId,
                rowsPerPage,
                page,
                sortNodeId,
                sortOrder,
                query,
            );
        }
        const {
            results,
            page: fetchedPage,
            total_count: totalCount,
            widget_labels: widgetLabels,
        } = await promise;

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

function deriveColumnData(
    config: { nodes?: string[] },
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

function deriveRelatedResourceColumnData(config: {
    additional_nodes?: string[];
}) {
    return [
        {
            nodeAlias: "@relation_name",
            widgetLabel: "Relation Name",
        },
        {
            nodeAlias: "@display_name",
            widgetLabel: "Display Name",
        },
        ...config.additional_nodes!.map((nodeAlias: string) => {
            return {
                nodeAlias,
                widgetLabel: widgetLabelLookup.value[nodeAlias] ?? nodeAlias,
            };
        }),
    ];
}

function getDisplayValue(
    tileData: Record<string, string | Record<string, unknown>>,
    key: string,
): string | null {
    if (key === "@relation_name") {
        return tileData["@relation_name"] as string;
    } else if (key === "@display_name") {
        return tileData["@display_name"] as string;
    } else if (
        tileData.nodes &&
        typeof tileData.nodes !== "string" &&
        key in tileData.nodes
    ) {
        return tileData.nodes[key] as string;
    }

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

function tileIdFromData(tileData: Record<string, unknown>): string {
    const { ["@has_children"]: _hasChildren, ...cards } = tileData;
    return Object.values(cards as Record<string, Record<string, string>>)[0][
        "@tile_id"
    ];
}

function onUpdateSortField(event: string) {
    // TODO: standardize node id/alias API param to avoid bifurcation.
    if (RELATED_RESOURCE_MODE) {
        sortNodeId.value = event;
        return;
    }
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

function rowClass(data: LabelBasedCard) {
    return [{ "no-children": data["@has_children"] === false }];
}
</script>

<template>
    <Message
        v-if="hasLoadingError"
        size="large"
        severity="error"
        icon="pi pi-times-circle"
    >
        {{ $gettext("An error occurred while fetching data.") }}
    </Message>
    <Message
        v-else-if="!isLoading && !query && !timeout && !searchResultsTotalCount"
        size="large"
        severity="info"
        icon="pi pi-info-circle"
    >
        {{ $gettext("No data found.") }}
    </Message>
    <div v-else>
        <DataTable
            :value="currentlyDisplayedTableData"
            :loading="isLoading"
            :total-records="searchResultsTotalCount"
            :expanded-rows="[]"
            :row-class
            @update:sort-field="onUpdateSortField"
            @update:sort-order="onUpdateSortOrder"
        >
            <template #header>
                <div
                    v-if="cardinality === CARDINALITY_N"
                    style="display: flex; justify-content: space-between"
                >
                    <div>
                        <span>{{ $gettext("Number of rows:") }}</span>
                        <Select
                            v-model="rowsPerPage"
                            style="margin: 0 1rem"
                            :options="rowsPerPageOptions"
                        />
                    </div>

                    <IconField style="display: flex">
                        <InputIcon
                            class="pi pi-search"
                            aria-hidden="true"
                        />
                        <InputText
                            v-model="query"
                            :placeholder="$gettext('Search')"
                            :aria-label="$gettext('Search')"
                        />
                    </IconField>
                </div>
            </template>

            <Column
                v-if="!RELATED_RESOURCE_MODE"
                expander
                style="width: 25px"
            />
            <Column
                v-for="columnDatum of columnData"
                :key="columnDatum.nodeAlias"
                :field="columnDatum.nodeAlias"
                :header="columnDatum.widgetLabel"
                :sortable="
                    RELATED_RESOURCE_MODE || cardinality === CARDINALITY_N
                "
            >
                <template #body="slotProps">
                    {{ getDisplayValue(slotProps.data, slotProps.field) }}
                </template>
            </Column>
            <template
                v-if="!RELATED_RESOURCE_MODE"
                #expansion="slotProps"
            >
                <HierarchicalTileViewer
                    :tile-id="tileIdFromData(slotProps.data)"
                />
            </template>
        </DataTable>

        <div
            v-if="searchResultsTotalCount > rowsPerPage"
            style="display: flex; justify-content: flex-end"
        >
            <Paginator
                :key="paginatorKey"
                :rows="rowsPerPage"
                :total-records="searchResultsTotalCount"
                @page="onUpdatePagination"
            />
        </div>
    </div>
</template>

<style scoped>
:deep(.p-paginator) {
    border-radius: 0;
}

:deep(.p-datatable-column-sorted) {
    background: var(--p-datatable-header-cell-background);
}

:deep(.p-datatable-row-toggle-button) {
    padding-block: 6px;
    width: var(--p-button-icon-width);
    height: var(--p-button-icon-height);
}

:deep(.no-children .p-datatable-row-toggle-button) {
    visibility: hidden;
}
</style>
