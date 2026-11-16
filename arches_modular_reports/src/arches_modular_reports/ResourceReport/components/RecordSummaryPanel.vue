<script setup lang="ts">
import { computed, ref, watch, watchEffect } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";

import { fetchEditHistory } from "@/arches_modular_reports/ResourceReport/api.ts";
import { useReportData } from "@/arches_modular_reports/ResourceReport/composables/useReportData.ts";
import { EMPTY_VALUE } from "@/arches_modular_reports/ResourceReport/constants.ts";
import {
    completenessCards,
    groupCardsByReportTab,
} from "@/arches_modular_reports/ResourceReport/utils/completeness.ts";
import {
    canAddTile,
    nodegroupTiles,
} from "@/arches_modular_reports/ResourceReport/utils/tiles.ts";

import type {
    ComponentNode,
    EditHistoryEntry,
} from "@/arches_modular_reports/ResourceReport/types.ts";
import type { CompletenessCard } from "@/arches_modular_reports/ResourceReport/utils/completeness.ts";

defineProps<{
    component: ComponentNode;
}>();

const { $gettext, $ngettext } = useGettext();
const reportData = useReportData();

const latestEdit = ref<EditHistoryEntry | null>(null);
const isLoadingLatestEdit = ref(true);
const latestEditError = ref<Error | null>(null);
let latestEditRequestNumber = 0;

const resourceInstanceId = computed(
    () => reportData.value.resource.resourceinstanceid,
);

const isEditable = computed(
    () => reportData.value.canEdit && reportData.value.editor.isAvailable,
);

const cards = computed(() =>
    completenessCards(
        reportData.value.nodegroupWidgetConfigs,
        reportData.value.resource.aliased_data,
        (tileId) => reportData.value.changeSet.isPendingDelete(tileId),
    ),
);

const filledCount = computed(
    () => cards.value.filter((card) => card.hasData).length,
);

const emptyCards = computed(() => cards.value.filter((card) => !card.hasData));

const requiredEmptyCount = computed(
    () => emptyCards.value.filter((card) => card.isRequired).length,
);

const lastUpdated = computed(() => {
    if (isLoadingLatestEdit.value) {
        return $gettext("Loading…");
    }
    if (latestEditError.value !== null) {
        return $gettext("Unavailable");
    }
    if (latestEdit.value === null) {
        return $gettext("No edits recorded");
    }
    return new Date(latestEdit.value.timestamp).toLocaleString(
        reportData.value.context.language,
        { dateStyle: "medium", timeStyle: "short" },
    );
});

const updatedBy = computed(() => latestEdit.value?.user || EMPTY_VALUE);

const filledSummary = computed(() =>
    $gettext("%{filled} of %{total}", {
        filled: String(filledCount.value),
        total: String(cards.value.length),
    }),
);

const emptySummary = computed(() => {
    const emptyCount = String(emptyCards.value.length);
    if (requiredEmptyCount.value === 0) {
        return emptyCount;
    }
    return $ngettext(
        "%{count}, including %{required} required",
        "%{count}, including %{required} required",
        requiredEmptyCount.value,
        { count: emptyCount, required: String(requiredEmptyCount.value) },
    );
});

const emptyCardGroups = computed(() =>
    groupCardsByReportTab(
        emptyCards.value,
        reportData.value.reportTabs,
        reportData.value.nodegroupWidgetConfigs,
    ).map((group, groupIndex) => ({
        headingId: `record-summary-panel-group-${groupIndex}`,
        label: groupLabel(group.tabLabel),
        cards: group.cards.map((card) => ({
            ...card,
            isAddable: isAddable(card),
        })),
    })),
);

watchEffect(() => {
    loadLatestEdit(resourceInstanceId.value);
});

// Applying edits adds to the edit history, so the latest edit changes too.
watch(
    () => reportData.value.changeSet.isSaving.value,
    (isSaving, wasSaving) => {
        if (
            wasSaving &&
            !isSaving &&
            reportData.value.changeSet.saveError.value === null
        ) {
            loadLatestEdit(resourceInstanceId.value);
        }
    },
);

async function loadLatestEdit(resourceId: string): Promise<void> {
    latestEditRequestNumber += 1;
    const requestNumber = latestEditRequestNumber;
    isLoadingLatestEdit.value = true;
    latestEditError.value = null;
    try {
        const historyPage = await fetchEditHistory(resourceId, null, "");
        if (requestNumber === latestEditRequestNumber) {
            latestEdit.value = historyPage.results[0] ?? null;
        }
    } catch (error) {
        if (requestNumber === latestEditRequestNumber) {
            latestEditError.value = error as Error;
        }
    } finally {
        if (requestNumber === latestEditRequestNumber) {
            isLoadingLatestEdit.value = false;
        }
    }
}

// A tab's own label; the leftover cards are "not in the report" only when the
// report has tabs to be in, and go unheaded otherwise.
function groupLabel(tabLabel: string | null): string {
    if (tabLabel !== null) {
        return tabLabel;
    }
    if (reportData.value.reportTabs.length > 0) {
        return $gettext("Not in the report");
    }
    return "";
}

// Same rule as the card's Add button in the data browser.
function isAddable(card: CompletenessCard): boolean {
    return (
        isEditable.value &&
        canAddTile(
            reportData.value.nodegroupWidgetConfigs[card.nodegroupAlias],
            nodegroupTiles(
                reportData.value.resource.aliased_data[card.nodegroupAlias],
            ).length,
            null,
            reportData.value.changeSet,
        )
    );
}

// Adds an entry to the card and opens it in the editor, as the card's Add
// button does; a card that can't take another entry is shown instead.
async function addToCard(card: CompletenessCard): Promise<void> {
    reportData.value.folioNavigation.jumpToNodegroup(card.nodegroupAlias);
    if (!isAddable(card)) {
        return;
    }
    const tileId = await reportData.value.changeSet.addTile(
        card.nodegroupAlias,
        null,
    );
    if (tileId !== null) {
        reportData.value.editor.open({
            nodegroupAlias: card.nodegroupAlias,
            tileId,
        });
    }
}
</script>

<template>
    <!-- The editor opens in this same column; it replaces the summary rather
         than covering it. -->
    <section
        v-if="reportData.editor.target === null"
        class="record-summary-panel"
        aria-labelledby="record-summary-panel-title"
    >
        <header class="record-summary-panel-bar">
            <h3
                id="record-summary-panel-title"
                class="record-summary-panel-caption"
            >
                {{ $gettext("Record Summary") }}
            </h3>
        </header>
        <div class="record-summary-panel-body">
            <section
                class="record-summary-panel-overview"
                aria-labelledby="record-summary-panel-overview-title"
            >
                <h4
                    id="record-summary-panel-overview-title"
                    class="record-summary-panel-heading"
                >
                    {{ $gettext("Resource Summary") }}
                </h4>
                <dl class="record-summary-panel-facts">
                    <div class="record-summary-panel-fact">
                        <dt>{{ $gettext("Last updated") }}</dt>
                        <dd>
                            <time
                                v-if="latestEdit !== null"
                                :datetime="latestEdit.timestamp"
                            >
                                {{ lastUpdated }}
                            </time>
                            <span v-else>{{ lastUpdated }}</span>
                        </dd>
                    </div>
                    <div class="record-summary-panel-fact">
                        <dt>{{ $gettext("Updated by") }}</dt>
                        <dd>{{ updatedBy }}</dd>
                    </div>
                    <div class="record-summary-panel-fact">
                        <dt>{{ $gettext("Cards with data") }}</dt>
                        <dd>{{ filledSummary }}</dd>
                    </div>
                    <div class="record-summary-panel-fact">
                        <dt>{{ $gettext("Cards without data") }}</dt>
                        <dd>{{ emptySummary }}</dd>
                    </div>
                </dl>
            </section>
            <section
                class="record-summary-panel-empty-cards"
                aria-labelledby="record-summary-panel-empty-title"
            >
                <h4
                    id="record-summary-panel-empty-title"
                    class="record-summary-panel-heading"
                >
                    {{ $gettext("Cards without data") }}
                </h4>
                <p
                    v-if="emptyCardGroups.length === 0"
                    class="record-summary-panel-none"
                >
                    {{ $gettext("Every card has data.") }}
                </p>
                <div
                    v-for="group in emptyCardGroups"
                    :key="group.headingId"
                    class="record-summary-panel-group"
                >
                    <h5
                        v-if="group.label !== ''"
                        :id="group.headingId"
                        class="record-summary-panel-group-label"
                    >
                        {{ group.label }}
                    </h5>
                    <ul
                        class="record-summary-panel-cards"
                        :aria-labelledby="
                            group.label !== '' ? group.headingId : undefined
                        "
                    >
                        <li
                            v-for="card in group.cards"
                            :key="card.nodegroupAlias"
                            class="record-summary-panel-card"
                        >
                            <Button
                                class="record-summary-panel-card-name"
                                variant="link"
                                size="small"
                                :label="card.name"
                                :aria-label="
                                    card.isAddable
                                        ? $gettext(
                                              'Add to %{card}',
                                              { card: card.name },
                                              true,
                                          )
                                        : $gettext(
                                              'Show %{card} in the data browser',
                                              { card: card.name },
                                              true,
                                          )
                                "
                                :disabled="
                                    card.isAddable &&
                                    reportData.changeSet.isBusy.value
                                "
                                @click="addToCard(card)"
                            />
                            <span
                                v-if="card.isRequired"
                                class="record-summary-panel-required"
                            >
                                {{ $gettext("(required)") }}
                            </span>
                        </li>
                    </ul>
                </div>
            </section>
        </div>
    </section>
</template>

<style scoped>
.record-summary-panel {
    display: flex;
    flex-direction: column;
    min-block-size: 100%;
    color: var(--p-text-muted-color);
    font-size: 1.3rem;
    line-height: 1.45;
}

.record-summary-panel-bar {
    position: sticky;
    inset-block-start: 0;
    z-index: 1;
    display: flex;
    flex-shrink: 0;
    align-items: center;
    block-size: var(--resource-report-bar-block-size);
    padding-inline: 1.6rem;
    border-block-end: 0.1rem solid var(--resource-report-bar-border-color);
    background: var(--resource-report-bar-background);
}

.record-summary-panel-caption,
.record-summary-panel-heading {
    margin: 0;
    color: var(--p-text-muted-color);
    font-size: 1.25rem;
    font-weight: 700;
    letter-spacing: 0.07rem;
    text-transform: uppercase;
}

.record-summary-panel-body {
    display: flex;
    flex-direction: column;
    gap: 2.4rem;
    padding-block: 2rem;
    padding-inline: 2.4rem;
}

.record-summary-panel-overview {
    display: flex;
    flex-direction: column;
    gap: 1.4rem;
}

.record-summary-panel-facts {
    display: grid;
    grid-template-columns: minmax(0, 14rem) minmax(0, 1fr);
    row-gap: 0.1rem;
    column-gap: 1.6rem;
    margin: 0;
}

/* Each row's dt and dd sit in the outer grid's two columns. */
.record-summary-panel-fact {
    display: contents;
}

.record-summary-panel-fact dd {
    margin: 0;
}

.record-summary-panel-empty-cards {
    display: flex;
    flex-direction: column;
    gap: 1.4rem;
}

.record-summary-panel-heading {
    padding-block-end: 0.6rem;
    border-block-end: 0.1rem solid var(--p-content-border-color);
}

.record-summary-panel-none {
    margin: 0;
}

.record-summary-panel-group {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
}

.record-summary-panel-group-label {
    margin: 0;
    font-size: 1.2rem;
    font-weight: 600;
}

.record-summary-panel-cards {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
    margin: 0;
    padding-inline-start: 1.4rem;
}

.record-summary-panel-card {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    gap: 0.6rem;
}

/* Muted like the rest of the panel, so the underline (always shown, not just
   on hover) is what marks the name as a link. */
.record-summary-panel-card .record-summary-panel-card-name {
    --p-button-link-color: var(--p-text-muted-color);
    --p-button-link-hover-color: var(--p-text-color);
    --p-button-link-active-color: var(--p-text-color);
    padding: 0;
    font-size: 1.3rem;
    text-align: start;
}

.record-summary-panel-card
    .record-summary-panel-card-name
    :deep(.p-button-label) {
    text-decoration: underline;
    text-decoration-color: var(--p-content-border-color);
    text-underline-offset: 0.3rem;
}

.record-summary-panel-card
    .record-summary-panel-card-name:not(:disabled):hover
    :deep(.p-button-label) {
    text-decoration-color: currentColor;
}

.record-summary-panel-required {
    color: var(--p-message-warn-color);
    font-size: 1.1rem;
    font-weight: 600;
}
</style>
