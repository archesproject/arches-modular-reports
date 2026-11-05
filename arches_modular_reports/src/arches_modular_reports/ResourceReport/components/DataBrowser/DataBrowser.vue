<script setup lang="ts">
import { computed } from "vue";
import { useGettext } from "vue3-gettext";

import IconField from "openvue/iconfield";
import InputIcon from "openvue/inputicon";
import InputText from "openvue/inputtext";

import DataFolio from "@/arches_modular_reports/ResourceReport/components/DataBrowser/components/DataFolio.vue";

import { useFilterQuery } from "@/arches_modular_reports/ResourceReport/composables/useFilterQuery.ts";
import { useReportData } from "@/arches_modular_reports/ResourceReport/composables/useReportData.ts";
import { folioMatches } from "@/arches_modular_reports/ResourceReport/utils/data-filter.ts";
import { childNodegroupAliases } from "@/arches_modular_reports/ResourceReport/utils/graph-nodes.ts";
import { nodegroupTiles } from "@/arches_modular_reports/ResourceReport/utils/tiles.ts";

import type { ComponentNode } from "@/arches_modular_reports/ResourceReport/types.ts";

defineProps<{
    component: ComponentNode;
}>();

const { $gettext } = useGettext();
const reportData = useReportData();

const { filterText, query: appliedFilterText } = useFilterQuery();

const query = computed(() => appliedFilterText.value.toLocaleLowerCase());

const isEditable = computed(
    () => reportData.value.canEdit && reportData.value.editor.isAvailable,
);

const folios = computed(() =>
    childNodegroupAliases(reportData.value.nodegroupWidgetConfigs, null)
        .map((nodegroupAlias) => ({
            nodegroupAlias,
            tiles: nodegroupTiles(
                reportData.value.resource.aliased_data[nodegroupAlias],
            ),
        }))
        .filter(
            (folio) =>
                query.value === "" ||
                folioMatches(
                    reportData.value.nodegroupWidgetConfigs,
                    folio.nodegroupAlias,
                    folio.tiles,
                    query.value,
                ),
        ),
);
</script>

<template>
    <div class="data-browser">
        <div class="data-browser-filter-bar">
            <IconField>
                <InputIcon class="pi pi-search" />
                <InputText
                    v-model="filterText"
                    class="data-browser-filter"
                    :placeholder="$gettext('Filter branches, groups, fields…')"
                    :aria-label="$gettext('Filter the data')"
                />
            </IconField>
        </div>
        <p
            v-if="query !== '' && folios.length === 0"
            class="data-browser-no-results"
        >
            {{
                $gettext(
                    "No results for “%{query}”",
                    { query: appliedFilterText },
                    true,
                )
            }}
        </p>
        <div class="data-browser-folios">
            <DataFolio
                v-for="folio in folios"
                :key="folio.nodegroupAlias"
                :nodegroup-alias="folio.nodegroupAlias"
                :nodegroup-widget-configs="reportData.nodegroupWidgetConfigs"
                :tiles="folio.tiles"
                :parent-tile-id="null"
                :change-set="reportData.changeSet"
                :query="query"
                :matched-by-ancestor="false"
                :selected-tile-id="reportData.editor.target?.tileId ?? null"
                :is-editable="isEditable"
                @edit-tile="reportData.editor.open"
            />
        </div>
    </div>
</template>

<style scoped>
.data-browser {
    display: flex;
    flex-direction: column;
}

.data-browser-filter-bar {
    position: sticky;
    inset-block-start: 0;
    z-index: 1;
    padding-block: 0.8rem 0.6rem;
    padding-inline: 2rem;
    border-block-end: 0.1rem solid var(--p-content-border-color);
    background: var(--resource-report-aside-background);
}

.data-browser-filter-bar .p-iconfield .data-browser-filter {
    inline-size: 100%;
    padding-block: 0.45rem;
    padding-inline-start: 3.1rem;
    border-color: var(--p-content-border-color);
    border-radius: 0.5rem;
    font-size: 1.2rem;
}

.data-browser-filter-bar .p-inputicon {
    color: var(--p-text-muted-color);
    font-size: 1.1rem;
}

.data-browser-folios {
    display: flex;
    flex-direction: column;
    padding: 1.6rem;
}

.data-browser-no-results {
    margin: 0;
    padding-block: 3.2rem;
    padding-inline: 1.6rem;
    color: var(--p-text-muted-color);
    font-size: 1.2rem;
    text-align: center;
}
</style>
