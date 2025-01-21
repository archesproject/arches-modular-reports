<script setup lang="ts">
import { computed, inject, onMounted, ref, watch } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "primevue/button";
import Column from "primevue/column";
import DataTable from "primevue/datatable";
import IconField from "primevue/iconfield";
import InputIcon from "primevue/inputicon";
import InputText from "primevue/inputtext";
import Message from "primevue/message";

import {
    ASC,
    DESC,
    ROWS_PER_PAGE_OPTIONS,
} from "@/arches_provenance/constants.ts";
import { fetchNodegroupTileData } from "@/arches_provenance/EditableReport/api.ts";
import HierarchicalTileViewer from "@/arches_provenance/EditableReport/components/HierarchicalTileViewer.vue";

import type { Ref } from "vue";
import type { DataTablePageEvent } from "primevue/datatable";
import type {
    LabelBasedCard,
    NodePresentationLookup,
} from "@/arches_provenance/EditableReport/types";

const props = defineProps<{
    component: {
        config: {
            nodegroup_id: string;
            nodes: string[];
        };
    };
    resourceInstanceId: string;
}>();

const { $gettext } = useGettext();
const CARDINALITY_N = "n";
const queryTimeoutValue = 500;
let timeout: ReturnType<typeof setTimeout> | null = null;

const tableTitle = ref("");
const rowsPerPage = ref(ROWS_PER_PAGE_OPTIONS[0]);
const currentPage = ref(1);
const query = ref("");
const sortField = ref("");
const direction = ref(ASC);
const currentlyDisplayedTableData = ref<unknown[]>([]);
const searchResultsTotalCount = ref(0);
const isLoading = ref(false);
const hasLoadingError = ref(false);
const resettingToFirstPage = ref(false);
const pageNumberToNodegroupTileData = ref<Record<number, unknown[]>>({});

const userCanEditResourceInstance = inject("userCanEditResourceInstance");
const nodePresentationLookup = inject("nodePresentationLookup") as Ref<
    NodePresentationLookup | undefined
>;

const first = computed(() => {
    if (resettingToFirstPage.value) {
        return 0;
    }
    return (currentPage.value - 1) * rowsPerPage.value;
});

const isEmpty = computed(
    () =>
        !isLoading.value &&
        !query.value &&
        !searchResultsTotalCount.value &&
        !timeout,
);

const nodeAliases = computed(() => {
    if (!nodePresentationLookup.value) {
        return [];
    }
    return (
        Object.entries(nodePresentationLookup.value)
            .filter(
                ([_nodeAlias, nodeDetails]) =>
                    nodeDetails.nodegroup.nodegroup_id ===
                    props.component.config.nodegroup_id,
            )
            .map((keyVal) => keyVal[0]) ?? []
    );
});

const columnData = computed(() => {
    if (!nodePresentationLookup.value) {
        return [];
    }
    return nodeAliases.value.map((nodeAlias) => {
        return {
            nodeAlias,
            widgetLabel: nodePresentationLookup.value![nodeAlias].widget_label,
        };
    });
});

const cardinality = computed(() => {
    if (!nodePresentationLookup.value) {
        return "";
    }
    return nodePresentationLookup.value[nodeAliases.value[0]].nodegroup
        .cardinality;
});

const cardName = computed(() => {
    if (!nodePresentationLookup.value) {
        return "";
    }
    return nodePresentationLookup.value[nodeAliases.value[0]].card_name;
});

function onPageTurn(event: DataTablePageEvent) {
    currentPage.value = resettingToFirstPage.value ? 1 : event.page + 1;
    rowsPerPage.value = event.rows;
}

function onUpdateSortOrder(event: number | undefined) {
    if (event === 1) {
        direction.value = ASC;
    } else if (event === -1) {
        direction.value = DESC;
    }
}

function rowClass(data: LabelBasedCard) {
    return [{ "no-children": data["@has_children"] === false }];
}

watch(query, () => {
    if (timeout) {
        clearTimeout(timeout);
    }

    timeout = setTimeout(() => {
        pageNumberToNodegroupTileData.value = {};
        resettingToFirstPage.value = true;
        fetchData(1);
    }, queryTimeoutValue);
});

watch([direction, sortField, rowsPerPage], () => {
    pageNumberToNodegroupTileData.value = {};
    resettingToFirstPage.value = true;
    fetchData(1);
});

watch(currentPage, () => {
    if (currentPage.value in pageNumberToNodegroupTileData.value) {
        currentlyDisplayedTableData.value =
            pageNumberToNodegroupTileData.value[currentPage.value];
    } else {
        resettingToFirstPage.value = false;
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

function tileIdFromData(tileData: Record<string, unknown>): string {
    const { ["@has_children"]: _hasChildren, ...cards } = tileData;
    return Object.values(cards as Record<string, Record<string, string>>)[0][
        "@tile_id"
    ];
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

onMounted(fetchData);
</script>

<template>
    <div style="display: flex; align-items: center">
        <h3>{{ tableTitle }}</h3>

        <Button
            v-if="
                userCanEditResourceInstance &&
                (isEmpty || cardinality === CARDINALITY_N)
            "
            :label="$gettext('Add %{cardName}', { cardName })"
            icon="pi pi-plus"
            variant="outlined"
            style="margin: 1rem 2rem 0 2rem"
        />
    </div>

    <Message
        v-if="hasLoadingError"
        size="large"
        severity="error"
        icon="pi pi-times-circle"
    >
        {{ $gettext("An error occurred while fetching data.") }}
    </Message>

    <Message
        v-else-if="isEmpty"
        size="large"
        severity="info"
        icon="pi pi-info-circle"
    >
        {{ $gettext("No data found.") }}
    </Message>
    <DataTable
        v-else
        :value="currentlyDisplayedTableData"
        :loading="isLoading"
        :total-records="searchResultsTotalCount"
        :expanded-rows="[]"
        :first
        :row-class
        paginator
        :always-show-paginator="
            searchResultsTotalCount >
            Math.min(rowsPerPage, ROWS_PER_PAGE_OPTIONS[0])
        "
        :lazy="true"
        :rows="rowsPerPage"
        :rows-per-page-options="ROWS_PER_PAGE_OPTIONS"
        :sortable="cardinality === CARDINALITY_N"
        @page="onPageTurn"
        @update:first="resettingToFirstPage = false"
        @update:sort-field="sortField = $event"
        @update:sort-order="onUpdateSortOrder"
    >
        <template #header>
            <div
                v-if="cardinality === CARDINALITY_N"
                style="display: flex; justify-content: flex-end"
            >
                <IconField style="display: flex">
                    <InputIcon
                        class="pi pi-search"
                        aria-hidden="true"
                        style="font-size: 1rem"
                    />
                    <InputText
                        v-model="query"
                        :placeholder="$gettext('Search')"
                        :aria-label="$gettext('Search')"
                    />
                </IconField>
            </div>
        </template>
        <template #empty>
            <Message
                size="large"
                severity="info"
                icon="pi pi-info-circle"
            >
                {{ $gettext("No results match your search.") }}
            </Message>
        </template>

        <Column
            expander
            style="width: 25px"
        />
        <Column
            v-for="columnDatum of columnData"
            :key="columnDatum.nodeAlias"
            :field="columnDatum.nodeAlias"
            :header="columnDatum.widgetLabel"
            :sortable="cardinality === CARDINALITY_N"
        >
            <template #body="slotProps">
                {{ getDisplayValue(slotProps.data, slotProps.field) }}
            </template>
        </Column>
        <Column v-if="userCanEditResourceInstance">
            <template #body>
                <div
                    style="
                        width: 100%;
                        display: flex;
                        justify-content: flex-end;
                    "
                >
                    <div
                        style="
                            display: flex;
                            justify-content: space-evenly;
                            width: 6rem;
                        "
                    >
                        <Button
                            icon="pi pi-pencil"
                            class="p-button-outlined"
                            :aria-label="$gettext('Edit')"
                            rounded
                        />
                        <Button
                            icon="pi pi-trash"
                            class="p-button-outlined"
                            severity="danger"
                            :aria-label="$gettext('Delete')"
                            rounded
                        />
                    </div>
                </div>
            </template>
        </Column>
        <template #expansion="slotProps">
            <HierarchicalTileViewer :tile-id="tileIdFromData(slotProps.data)" />
        </template>
    </DataTable>
</template>

<style scoped>
:deep(.p-datatable-column-sorted) {
    background: var(--p-datatable-header-cell-background);
}

:deep(.no-children .p-datatable-row-toggle-button) {
    visibility: hidden;
}

:deep(.p-paginator) {
    justify-content: end;
}
</style>
