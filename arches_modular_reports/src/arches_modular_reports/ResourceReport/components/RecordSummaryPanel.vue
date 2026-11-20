<script setup lang="ts">
import { computed, useId } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";

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

import type { ComponentNode } from "@/arches_modular_reports/ResourceReport/types.ts";
import type { CompletenessCard } from "@/arches_modular_reports/ResourceReport/utils/completeness.ts";

defineProps<{
    component: ComponentNode;
}>();

const { $gettext } = useGettext();
const reportData = useReportData();
const titleId = useId();
const overviewTitleId = useId();
const emptyCardsTitleId = useId();
const groupIdPrefix = useId();

const isEditable = computed(
    () => reportData.value.canEdit && reportData.value.editor.isAvailable,
);

const latestEdit = computed(() => reportData.value.context.latest_edit);

const cards = computed(() =>
    completenessCards(
        reportData.value.nodegroupWidgetConfigs,
        reportData.value.resource.aliased_data,
        (tileId) => reportData.value.changeSet.isPendingDelete(tileId),
        reportData.value.nodeTextContext,
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
    return $gettext("%{count}, including %{required} required", {
        count: emptyCount,
        required: String(requiredEmptyCount.value),
    });
});

const emptyCardGroups = computed(() =>
    groupCardsByReportTab(
        emptyCards.value,
        reportData.value.reportTabs,
        reportData.value.nodegroupWidgetConfigs,
    ).map((group, groupIndex) => {
        const headingId = `${groupIdPrefix}-${groupIndex}`;
        const label = groupLabel(group.tabLabel);
        return {
            headingId,
            label,
            labelledBy: label === "" ? undefined : headingId,
            cards: group.cards.map((card) => ({
                ...card,
                isAddable: isAddable(card),
                actionLabel: cardActionLabel(card),
            })),
        };
    }),
);

function groupLabel(tabLabel: string | null): string {
    if (tabLabel !== null) {
        return tabLabel;
    }
    if (reportData.value.reportTabs.length > 0) {
        return $gettext("Not in the report");
    }
    return "";
}

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

function cardActionLabel(card: CompletenessCard): string {
    if (isAddable(card)) {
        return $gettext("Add to %{card}", { card: card.name }, true);
    }
    return $gettext(
        "Show %{card} in the data browser",
        { card: card.name },
        true,
    );
}

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
    <section
        v-if="reportData.editor.target === null"
        class="record-summary-panel"
        :aria-labelledby="titleId"
    >
        <header class="record-summary-panel-bar">
            <h3
                :id="titleId"
                class="record-summary-panel-caption"
            >
                {{ $gettext("Record Summary") }}
            </h3>
        </header>
        <div class="record-summary-panel-body">
            <section
                class="record-summary-panel-overview"
                :aria-labelledby="overviewTitleId"
            >
                <h4
                    :id="overviewTitleId"
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
                :aria-labelledby="emptyCardsTitleId"
            >
                <h4
                    :id="emptyCardsTitleId"
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
                        :aria-labelledby="group.labelledBy"
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
                                :aria-label="card.actionLabel"
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
