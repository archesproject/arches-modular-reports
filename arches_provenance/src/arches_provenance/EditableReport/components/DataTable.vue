<script setup lang="ts">
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

import type {
    ColumnDatum,
    LabelBasedCard,
} from "@/arches_provenance/EditableReport/types";

interface ExpansionProps {
    // primevue uses explicit any
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    data: any;
    index: number;
}

const { $gettext } = useGettext();

defineProps<{
    mode: "data" | "related-resources";
    config: {
        nodegroup_id?: string;
        nodes?: string[];
        graph_id?: string;
        additional_nodes?: string[];
    };
    columnData: ColumnDatum[];
    currentlyDisplayedTableData: unknown[];
    searchResultsTotalCount: number;
    isLoading: boolean;
    hasLoadingError: boolean;
    isEmpty: boolean;
    sortable: boolean;
    getDisplayValue: (
        data: Record<string, string | Record<string, unknown>>,
        key: string,
    ) => string | null;
}>();

const currentPage = defineModel<number>("currentPage");
const rowsPerPage = defineModel<number>("rowsPerPage");

const sortField = defineModel<string>("sortField");
const direction = defineModel<string>("direction");
const query = defineModel<string>("query");

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
        :row-class
        paginator
        :always-show-paginator="
            searchResultsTotalCount >
            Math.min(rowsPerPage!, ROWS_PER_PAGE_OPTIONS[0])
        "
        :lazy="true"
        :rows="rowsPerPage"
        :rows-per-page-options="ROWS_PER_PAGE_OPTIONS"
        @page="(currentPage = $event.page + 1) && (rowsPerPage = $event.rows)"
        @update:sort-field="sortField = $event"
        @update:sort-order="onUpdateSortOrder"
    >
        <template #header>
            <div
                v-if="sortable"
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
            v-if="mode === 'data'"
            expander
            style="width: 25px"
        />
        <Column
            v-for="columnDatum of columnData"
            :key="columnDatum.nodeAlias"
            :field="columnDatum.nodeAlias"
            :header="columnDatum.widgetLabel"
            :sortable="sortable"
        >
            <template #body="slotProps">
                {{ getDisplayValue(slotProps.data, slotProps.field) }}
            </template>
        </Column>
        <template #expansion="slotProps: ExpansionProps">
            <slot
                name="expansion"
                :data="slotProps.data"
            />
        </template>
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
