<script setup lang="ts">
import arches from "arches";

import { computed, onMounted, ref, watch } from "vue";
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
import { fetchRelatedResourceData } from "@/arches_provenance/EditableReport/api.ts";

import type { DataTablePageEvent } from "primevue/datatable";

const props = defineProps<{
    component: {
        config: {
            additional_nodes: string[];
            graph_id: string;
        };
    };
    resourceInstanceId: string;
}>();

const { $gettext } = useGettext();

const queryTimeoutValue = 500;
let timeout: ReturnType<typeof setTimeout> | null = null;

const rowsPerPage = ref(ROWS_PER_PAGE_OPTIONS[0]);
const currentPage = ref(1);
const query = ref("");
const sortField = ref("@relation_name");
const direction = ref(ASC);
const currentlyDisplayedTableData = ref<unknown[]>([]);
const searchResultsTotalCount = ref(0);
const isLoading = ref(false);
const hasLoadingError = ref(false);
const widgetLabelLookup = ref<Record<string, string>>({});
const resettingToFirstPage = ref(false);

const pageNumberToNodegroupTileData = ref<Record<number, unknown[]>>({});

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
    return null;
}

function getRelatedResourceIds(
    tileData: Record<string, string | Record<string, unknown>>,
    key: string,
): string[] {
    if (key === "@relation_name") {
        return [];
    } else if (key === "@display_name") {
        return [tileData.related_resource_id as string];
    } else if (
        tileData.nodes &&
        typeof tileData.nodes !== "string" &&
        key in tileData.nodes
    ) {
        return ["TODO"];
    }
    return [];
}

async function fetchData(requested_page: number = 1) {
    isLoading.value = true;

    try {
        const { results, page, total_count, widget_labels } =
            await fetchRelatedResourceData(
                props.resourceInstanceId,
                props.component.config.graph_id,
                props.component.config.additional_nodes!,
                rowsPerPage.value,
                requested_page,
                sortField.value,
                direction.value,
                query.value,
            );

        pageNumberToNodegroupTileData.value[page] = results;
        currentlyDisplayedTableData.value = results;
        currentPage.value = page;
        searchResultsTotalCount.value = total_count;
        widgetLabelLookup.value = widget_labels;
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
        paginator
        :always-show-paginator="
            searchResultsTotalCount >
            Math.min(rowsPerPage, ROWS_PER_PAGE_OPTIONS[0])
        "
        :lazy="true"
        :rows="rowsPerPage"
        :rows-per-page-options="ROWS_PER_PAGE_OPTIONS"
        :sortable="true"
        @page="onPageTurn"
        @update:first="resettingToFirstPage = false"
        @update:sort-field="sortField = $event"
        @update:sort-order="onUpdateSortOrder"
    >
        <template #header>
            <div style="display: flex; justify-content: flex-end">
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
            v-for="columnDatum of columnData"
            :key="columnDatum.nodeAlias"
            :field="columnDatum.nodeAlias"
            :header="columnDatum.widgetLabel"
            :sortable="true"
        >
        <template #body="{ data, field }">
                <template
                    v-if="
                        field !== '@relation_name' &&
                        getRelatedResourceIds(data, field).length
                    "
                >
                    <template
                        v-for="(item, index) in getRelatedResourceIds(
                            data,
                            field,
                        )"
                        :key="item"
                    >
                        <span v-if="index !== 0">, </span>
                        <Button
                            as="a"
                            variant="link"
                            :href="arches.urls.resource_report + item"
                            style="font-size: inherit; padding: 0"
                        >
                            {{ getDisplayValue(data, field) }}
                        </Button>
                    </template>
                </template>
                <template v-else>
                    {{ getDisplayValue(data, field) }}
                </template>
            </template>
        </Column>
    </DataTable>
</template>

<style scoped>
:deep(.p-datatable-column-sorted) {
    background: var(--p-datatable-header-cell-background);
}

:deep(.p-paginator) {
    justify-content: end;
}
</style>
