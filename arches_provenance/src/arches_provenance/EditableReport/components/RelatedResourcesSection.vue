<script setup lang="ts">
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
            node_aliases: string[];
            graph_slug: string;
            custom_labels: Record<string, string>;
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
const graphName = ref("");
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
        ...props.component.config.node_aliases.map((nodeAlias: string) => {
            return {
                nodeAlias,
                widgetLabel:
                    props.component.config.custom_labels?.[nodeAlias] ??
                    widgetLabelLookup.value[nodeAlias] ??
                    nodeAlias,
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

async function fetchData(requested_page: number = 1) {
    isLoading.value = true;

    try {
        const { results, page, total_count, graph_name, widget_labels } =
            await fetchRelatedResourceData(
                props.resourceInstanceId,
                props.component.config.graph_slug,
                props.component.config.node_aliases,
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
        graphName.value = graph_name;
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
    <h3>{{ graphName }}</h3>
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
                <Button
                    v-for="link in data[field].links"
                    :key="JSON.stringify(link)"
                    as="a"
                    variant="link"
                    target="_blank"
                    :href="link.link"
                    class="node-value-link"
                >
                    {{ link.label }}
                </Button>
                <template v-if="data[field].links.length === 0">
                    {{ data[field].display_value }}
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

.node-value-link {
    display: block;
    width: fit-content;
    font-size: inherit;
    padding: 0;
}
</style>
