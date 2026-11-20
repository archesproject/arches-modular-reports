<script setup lang="ts">
import { computed, onMounted, onUnmounted, useTemplateRef } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";
import IconField from "openvue/iconfield";
import InputIcon from "openvue/inputicon";
import InputText from "openvue/inputtext";

import DataFolio from "@/arches_modular_reports/ResourceReport/components/DataBrowser/components/DataFolio.vue";

import { useFilterQuery } from "@/arches_modular_reports/ResourceReport/composables/useFilterQuery.ts";
import { useReportData } from "@/arches_modular_reports/ResourceReport/composables/useReportData.ts";
import { folioMatches } from "@/arches_modular_reports/ResourceReport/utils/data-filter.ts";
import { childNodegroupAliases } from "@/arches_modular_reports/ResourceReport/utils/graph-nodes.ts";
import { nodegroupTiles } from "@/arches_modular_reports/ResourceReport/utils/tiles.ts";

import type { ComponentPublicInstance } from "vue";
import type { ComponentNode } from "@/arches_modular_reports/ResourceReport/types.ts";

defineProps<{
    component: ComponentNode;
}>();

const { $gettext } = useGettext();
const reportData = useReportData();

const { filterText, query: appliedFilterText } = useFilterQuery();
const filterInput = useTemplateRef<ComponentPublicInstance>("filterInput");

const unregisterFolioByAlias = new Map<string, () => void>();
let unregisterRevealer = (): void => undefined;

const query = computed(() => appliedFilterText.value.toLocaleLowerCase());

const isEditable = computed(
    () => reportData.value.canEdit && reportData.value.editor.isAvailable,
);

const topLevelAliases = computed(() =>
    childNodegroupAliases(reportData.value.nodegroupWidgetConfigs, null),
);

const flashedNodegroupAlias = computed(
    () => reportData.value.folioNavigation.flashedNodegroupAlias.value,
);

const folios = computed(() =>
    topLevelAliases.value
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
                    reportData.value.nodeTextContext,
                ),
        ),
);

onMounted(() => {
    unregisterRevealer = reportData.value.folioNavigation.registerRevealer({
        isLocal: true,
        contains: (nodegroupAlias) =>
            topLevelAliases.value.includes(nodegroupAlias),
        reveal: (nodegroupAlias) => {
            const isShown = folios.value.some(
                (folio) => folio.nodegroupAlias === nodegroupAlias,
            );
            if (!isShown) {
                clearFilter();
            }
        },
    });
});

onUnmounted(() => {
    unregisterRevealer();
    unregisterFolioByAlias.forEach((unregisterFolio) => unregisterFolio());
    unregisterFolioByAlias.clear();
});

function clearFilter(): void {
    filterText.value = "";
    appliedFilterText.value = "";
}

function clearFilterFromButton(): void {
    clearFilter();
    (filterInput.value?.$el as HTMLInputElement | undefined)?.focus();
}

function trackFolioElement(
    nodegroupAlias: string,
    element: Element | ComponentPublicInstance | null,
): void {
    unregisterFolioByAlias.get(nodegroupAlias)?.();
    unregisterFolioByAlias.delete(nodegroupAlias);
    if (element instanceof HTMLElement) {
        unregisterFolioByAlias.set(
            nodegroupAlias,
            reportData.value.folioNavigation.registerFolio(
                nodegroupAlias,
                element,
            ),
        );
    }
}
</script>

<template>
    <div class="data-browser">
        <div class="data-browser-filter-bar">
            <IconField>
                <InputIcon class="pi pi-search" />
                <InputText
                    ref="filterInput"
                    v-model="filterText"
                    class="data-browser-filter"
                    :placeholder="$gettext('Filter branches, groups, fields…')"
                    :aria-label="$gettext('Filter the data')"
                />
                <Button
                    v-if="filterText"
                    class="p-inputicon data-browser-filter-clear"
                    icon="pi pi-times"
                    variant="text"
                    :aria-label="$gettext('Clear filter')"
                    :title="$gettext('Clear filter')"
                    @click="clearFilterFromButton"
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
            <div
                v-for="folio in folios"
                :key="folio.nodegroupAlias"
                :ref="
                    (element) =>
                        trackFolioElement(folio.nodegroupAlias, element)
                "
                class="data-browser-folio"
                tabindex="-1"
                :class="{
                    'data-browser-folio-flash':
                        flashedNodegroupAlias === folio.nodegroupAlias,
                }"
                @animationend.self="reportData.folioNavigation.clearFlash"
            >
                <DataFolio
                    :nodegroup-alias="folio.nodegroupAlias"
                    :nodegroup-widget-configs="
                        reportData.nodegroupWidgetConfigs
                    "
                    :tiles="folio.tiles"
                    :parent-tile-id="null"
                    :change-set="reportData.changeSet"
                    :query="query"
                    :matched-by-ancestor="false"
                    :selected-tile-id="reportData.editor.target?.tileId ?? null"
                    :is-editable="isEditable"
                    :is-revealed="
                        flashedNodegroupAlias === folio.nodegroupAlias
                    "
                    :node-text-context="reportData.nodeTextContext"
                    :language-names="reportData.context.languages"
                    @edit-tile="reportData.editor.open"
                />
            </div>
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
    background: var(--resource-report-panel-background);
}

.data-browser-filter-bar .p-iconfield .data-browser-filter {
    inline-size: 100%;
    padding-block: 0.45rem;
    padding-inline: 3.1rem;
    border-color: var(--p-content-border-color);
    border-radius: 0.5rem;
    font-size: 1.2rem;
}

.data-browser-filter-bar .p-inputicon {
    color: var(--p-text-muted-color);
    font-size: 1.1rem;
}

.data-browser-filter-bar .data-browser-filter-clear {
    inline-size: auto;
    block-size: auto;
    padding: 0;
    border: none;
    background: none;
    color: var(--p-text-muted-color);
}

.data-browser-filter-bar .data-browser-filter-clear :deep(.p-button-icon) {
    font-size: inherit;
}

.data-browser-filter-bar .data-browser-filter-clear:not(:disabled):hover {
    border: none;
    background: none;
    color: var(--p-text-color);
}

.data-browser-filter-bar .data-browser-filter-clear:focus-visible {
    outline: 0.2rem solid var(--p-focus-ring-color);
    outline-offset: 0.2rem;
    border-radius: 0.2rem;
}

.data-browser-folios {
    display: flex;
    flex-direction: column;
    padding: 1.6rem;
}

.data-browser-folio:focus-visible {
    outline: 0.2rem solid var(--p-focus-ring-color);
    outline-offset: 0.2rem;
}

.data-browser-folio-flash {
    animation: data-browser-folio-flash 1.6s ease-out;
}

@keyframes data-browser-folio-flash {
    from {
        background: var(--p-highlight-background);
        box-shadow: 0 0 0 0.8rem var(--p-highlight-background);
    }
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
