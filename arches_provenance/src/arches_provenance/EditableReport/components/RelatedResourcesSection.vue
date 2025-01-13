<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

import { useGettext } from "vue3-gettext";

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

const pageNumberToNodegroupTileData = ref<Record<number, unknown[]>>({});

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
        fetchData(1);
    }, queryTimeoutValue);
});

watch([direction, sortField, rowsPerPage], () => {
    pageNumberToNodegroupTileData.value = {};
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
    <DataTable
        v-else
        :value="currentlyDisplayedTableData"
        :loading="isLoading"
        :total-records="searchResultsTotalCount"
        :expanded-rows="[]"
        paginator
        :always-show-paginator="
            searchResultsTotalCount >
            Math.min(rowsPerPage, ROWS_PER_PAGE_OPTIONS[0])
        "
        :lazy="true"
        :rows="rowsPerPage"
        :rows-per-page-options="ROWS_PER_PAGE_OPTIONS"
        :sortable="true"
        @page="(currentPage = $event.page + 1) && (rowsPerPage = $event.rows)"
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
            <template #body="slotProps">
                {{ getDisplayValue(slotProps.data, slotProps.field) }}
            </template>
        </Column>
    </DataTable>
</template>

<style scoped>
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
