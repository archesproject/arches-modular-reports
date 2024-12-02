<script setup lang="ts">
import { ref, onMounted, watch } from "vue";
import { useGettext } from "vue3-gettext";

import Column from "primevue/column";
import DataTable from "primevue/datatable";
import Select from "primevue/select";
import Paginator from "primevue/paginator";

import { useToast } from "primevue/usetoast";

import { DEFAULT_ERROR_TOAST_LIFE } from "@/arches_provenance/constants.ts";
import {
    fetchCardFromNodegroupId,
    fetchNodegroupTileData,
} from "@/arches_provenance/EditableReport/api.ts";

import type { Ref } from "vue";

const { $gettext } = useGettext();
const toast = useToast();

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
const currentPage = ref(1);
const searchResultsTotalCount = ref(0);
const query = ref("");

const tableTitle = ref("");
const columnNames: Ref<ColumnName[]> = ref([]);

const cardData = ref(null);
const pageNumberToNodegroupTileData = ref({});
const currentlyDisplayedTableData = ref([]);

const rowsPerPageOptions = ref([5, 10, 20]);
const rowsPerPage = ref(5);

const aaa = ref(0);

watch(
    rowsPerPage,
    async (newValue) => {
        aaa.value += 1;

        const { results, page, totalCount } = await fetchData(
            props.resourceInstanceId,
            props.component.config?.nodegroup_id,
            newValue,
            1,
        );

        pageNumberToNodegroupTileData.value = {
            [page]: results,
        };

        currentlyDisplayedTableData.value =
            pageNumberToNodegroupTileData.value[page];

        currentPage.value = page;
        searchResultsTotalCount.value = totalCount;
    },
    { immediate: true },
);

onMounted(() => {
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

async function fetchData(
    resourceInstanceId: string,
    nodegroupId: string,
    rowsPerPage: number,
    page: number,
) {
    isLoading.value = true;

    try {
        const fetchedNodegroupTileData = await fetchNodegroupTileData(
            resourceInstanceId,
            nodegroupId,
            rowsPerPage,
            page,
        );

        return {
            results: fetchedNodegroupTileData.results,
            page: fetchedNodegroupTileData.page,
            totalCount: fetchedNodegroupTileData.total_count,
        };
    } catch (error: unknown) {
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

async function foo(page) {
    if (pageNumberToNodegroupTileData.value[page]) {
        currentlyDisplayedTableData.value =
            pageNumberToNodegroupTileData.value[page];
        currentPage.value = page;
    } else {
        const {
            results,
            page: fetchedPage,
            totalCount,
        } = await fetchData(
            props.resourceInstanceId,
            props.component.config?.nodegroup_id,
            rowsPerPage.value,
            page,
        );

        pageNumberToNodegroupTileData.value[fetchedPage] = results;
        currentlyDisplayedTableData.value = results;
        currentPage.value = fetchedPage;
        searchResultsTotalCount.value = totalCount;
    }
}
</script>

<template>
    <DataTable
        v-if="currentlyDisplayedTableData.length > 0"
        :value="currentlyDisplayedTableData"
        :loading="isLoading"
        :total-records="searchResultsTotalCount"
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
    </DataTable>

    <Paginator
        :key="aaa"
        :rows="rowsPerPage"
        :total-records="searchResultsTotalCount"
        @page="(e) => foo(e.page + 1)"
    />

    <!-- <pre>{{ columnNames }}</pre> -->
    <!-- <pre>{{ props.component.config }}</pre> -->
    <!-- <pre>{{ cardData }}</pre> -->
    <!-- <pre>{{ pageNumberToNodegroupTileData }}</pre> -->
</template>

<style scoped>
:deep(.p-paginator) {
    border-radius: 0;
}
</style>
