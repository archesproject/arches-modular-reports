<script setup lang="ts">
import { computed, ref, watchEffect } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";
import IconField from "openvue/iconfield";
import InputIcon from "openvue/inputicon";
import InputText from "openvue/inputtext";
import Message from "openvue/message";
import Tag from "openvue/tag";

import { useReportData } from "@/arches_modular_reports/ResourceReport/composables/useReportData.ts";
import { fetchEditHistory } from "@/arches_modular_reports/ResourceReport/api.ts";
import { useFilterQuery } from "@/arches_modular_reports/ResourceReport/composables/useFilterQuery.ts";
import { PANEL_COUNT_EVENT } from "@/arches_modular_reports/ResourceReport/constants.ts";
import { readableText } from "@/arches_modular_reports/ResourceReport/utils/localized-text.ts";

import type {
    ComponentNode,
    DrawerPanelCount,
    EditHistoryEntry,
    EditHistoryValue,
    LabelledConfig,
    TagSeverity,
} from "@/arches_modular_reports/ResourceReport/types.ts";

const TILE_CREATE = "tile create";
const TILE_EDIT = "tile edit";
const TILE_DELETE = "tile delete";

defineProps<{
    component: ComponentNode<LabelledConfig>;
}>();

const emit = defineEmits<{
    (event: typeof PANEL_COUNT_EVENT, panelCount: DrawerPanelCount): void;
}>();

const { $gettext, $ngettext } = useGettext();
const reportData = useReportData();
const { filterText, query } = useFilterQuery();

const entries = ref<EditHistoryEntry[]>([]);
const nextCursor = ref<string | null>(null);
const isLoading = ref(false);
const loadError = ref<Error | null>(null);
const fullyShownEntryIds = ref(new Set<string>());
let latestHistoryRequestNumber = 0;

const resourceInstanceId = computed(
    () => reportData.value.resource.resourceinstanceid,
);

watchEffect(() => {
    loadHistory(query.value, null);
});

async function loadHistory(
    searchText: string,
    cursor: string | null,
): Promise<void> {
    latestHistoryRequestNumber += 1;
    const historyRequestNumber = latestHistoryRequestNumber;
    isLoading.value = true;
    loadError.value = null;
    try {
        const historyPage = await fetchEditHistory(
            resourceInstanceId.value,
            cursor,
            searchText,
        );
        if (historyRequestNumber !== latestHistoryRequestNumber) {
            return;
        }
        if (cursor === null) {
            entries.value = historyPage.results;
        } else {
            entries.value = [...entries.value, ...historyPage.results];
        }
        nextCursor.value = historyPage.next_cursor;
        if (searchText === "" && cursor === null) {
            emit(PANEL_COUNT_EVENT, {
                count: historyPage.results.length,
                hasMore: historyPage.next_cursor !== null,
            });
        }
    } catch (error) {
        if (historyRequestNumber === latestHistoryRequestNumber) {
            loadError.value = error as Error;
        }
    } finally {
        if (historyRequestNumber === latestHistoryRequestNumber) {
            isLoading.value = false;
        }
    }
}

function loadMore(): void {
    loadHistory(query.value, nextCursor.value);
}

function editTypeSeverity(entry: EditHistoryEntry): TagSeverity {
    if (entry.edit_type === TILE_CREATE) {
        return "success";
    }
    if (entry.edit_type === TILE_EDIT) {
        return "info";
    }
    if (entry.edit_type === TILE_DELETE) {
        return "danger";
    }
    return "secondary";
}

function formatTimestamp(timestamp: string): string {
    return new Date(timestamp).toLocaleString(
        reportData.value.context.language,
    );
}

function fieldLabel(nodeAlias: string): string {
    return reportData.value.graphNodesByAlias[nodeAlias].label;
}

function unchangedFieldCount(entry: EditHistoryEntry): number {
    return entry.values.filter((value) => !value.changed).length;
}

function hasHideableFields(entry: EditHistoryEntry): boolean {
    const unchangedCount = unchangedFieldCount(entry);
    return unchangedCount > 0 && unchangedCount < entry.values.length;
}

function isShowingAllFields(entry: EditHistoryEntry): boolean {
    return fullyShownEntryIds.value.has(entry.editlogid);
}

function valueText(nodeAlias: string, value: string | null): string {
    if (value === null) {
        return "";
    }
    return readableText(nodeAlias, value, reportData.value.nodeTextContext);
}

function displayedValues(entry: EditHistoryEntry): EditHistoryValue[] {
    if (!hasHideableFields(entry) || isShowingAllFields(entry)) {
        return entry.values;
    }
    return entry.values.filter((value) => value.changed);
}

function isMarkedChanged(
    entry: EditHistoryEntry,
    value: EditHistoryValue,
): boolean {
    return (
        value.changed && hasHideableFields(entry) && isShowingAllFields(entry)
    );
}

function fieldsToggleLabel(entry: EditHistoryEntry): string {
    if (isShowingAllFields(entry)) {
        return $gettext("Show changed fields only");
    }
    const unchangedCount = unchangedFieldCount(entry);
    return $ngettext(
        "Show %{count} unchanged field",
        "Show %{count} unchanged fields",
        unchangedCount,
        { count: String(unchangedCount) },
    );
}

function toggleAllFields(entry: EditHistoryEntry): void {
    const nextIds = new Set(fullyShownEntryIds.value);
    if (nextIds.has(entry.editlogid)) {
        nextIds.delete(entry.editlogid);
    } else {
        nextIds.add(entry.editlogid);
    }
    fullyShownEntryIds.value = nextIds;
}
</script>

<template>
    <div class="edit-history">
        <IconField>
            <InputIcon class="pi pi-search" />
            <InputText
                v-model="filterText"
                class="edit-history-filter"
                :placeholder="$gettext('Filter by card, user or change type…')"
                :aria-label="$gettext('Filter the edit history')"
            />
            <Button
                v-if="filterText"
                class="p-inputicon edit-history-filter-clear"
                icon="pi pi-times"
                variant="text"
                :aria-label="$gettext('Clear filter')"
                :title="$gettext('Clear filter')"
                @click="filterText = ''"
            />
        </IconField>
        <Message
            v-if="loadError"
            severity="error"
        >
            <span>
                {{
                    $gettext(
                        "Unable to load the edit history: %{message}",
                        { message: loadError.message },
                        true,
                    )
                }}
            </span>
        </Message>
        <p
            v-else-if="!isLoading && entries.length === 0 && query"
            class="edit-history-empty"
        >
            {{
                $gettext('No history entries match "%{query}"', { query }, true)
            }}
        </p>
        <p
            v-else-if="!isLoading && entries.length === 0"
            class="edit-history-empty"
        >
            {{ $gettext("No history entries yet.") }}
        </p>
        <ol class="edit-history-entries">
            <li
                v-for="entry in entries"
                :key="entry.editlogid"
                class="edit-history-entry"
            >
                <div class="edit-history-meta">
                    <Tag
                        :value="entry.edit_type_label"
                        :severity="editTypeSeverity(entry)"
                    />
                    <span
                        v-if="entry.card_name"
                        class="edit-history-card"
                    >
                        {{ entry.card_name }}
                    </span>
                    <span class="edit-history-user">
                        <i
                            class="pi pi-user"
                            aria-hidden="true"
                        />
                        <span>{{ entry.user }}</span>
                    </span>
                </div>
                <time
                    class="edit-history-time"
                    :datetime="entry.timestamp"
                >
                    {{ formatTimestamp(entry.timestamp) }}
                </time>
                <div
                    v-if="entry.values.length > 0"
                    class="edit-history-diff"
                >
                    <div class="edit-history-state">
                        <span class="edit-history-state-label">
                            {{ $gettext("Before") }}
                        </span>
                        <p
                            v-if="entry.edit_type === TILE_CREATE"
                            class="edit-history-empty"
                        >
                            {{ $gettext("No prior state — tile was created") }}
                        </p>
                        <dl
                            v-else
                            class="edit-history-fields"
                        >
                            <div
                                v-for="value in displayedValues(entry)"
                                :key="value.node_alias"
                                class="edit-history-field"
                                :class="{
                                    'edit-history-field-changed': value.changed,
                                }"
                            >
                                <dt>
                                    {{
                                        $gettext(
                                            "%{label}:",
                                            {
                                                label: fieldLabel(
                                                    value.node_alias,
                                                ),
                                            },
                                            true,
                                        )
                                    }}
                                </dt>
                                <dd>
                                    <span>{{
                                        valueText(
                                            value.node_alias,
                                            value.before,
                                        )
                                    }}</span>
                                    <span
                                        v-if="isMarkedChanged(entry, value)"
                                        class="edit-history-changed-marker"
                                    >
                                        <i
                                            class="pi pi-pencil"
                                            aria-hidden="true"
                                        />
                                        <span class="edit-history-sr-only">
                                            {{ $gettext("(changed)") }}
                                        </span>
                                    </span>
                                </dd>
                            </div>
                        </dl>
                    </div>
                    <div class="edit-history-state">
                        <span class="edit-history-state-label">
                            {{ $gettext("After") }}
                        </span>
                        <p
                            v-if="entry.edit_type === TILE_DELETE"
                            class="edit-history-empty"
                        >
                            {{ $gettext("Tile was deleted") }}
                        </p>
                        <dl
                            v-else
                            class="edit-history-fields"
                        >
                            <div
                                v-for="value in displayedValues(entry)"
                                :key="value.node_alias"
                                class="edit-history-field"
                                :class="{
                                    'edit-history-field-changed': value.changed,
                                }"
                            >
                                <dt>
                                    {{
                                        $gettext(
                                            "%{label}:",
                                            {
                                                label: fieldLabel(
                                                    value.node_alias,
                                                ),
                                            },
                                            true,
                                        )
                                    }}
                                </dt>
                                <dd>
                                    <span>{{
                                        valueText(value.node_alias, value.after)
                                    }}</span>
                                    <span
                                        v-if="isMarkedChanged(entry, value)"
                                        class="edit-history-changed-marker"
                                    >
                                        <i
                                            class="pi pi-pencil"
                                            aria-hidden="true"
                                        />
                                        <span class="edit-history-sr-only">
                                            {{ $gettext("(changed)") }}
                                        </span>
                                    </span>
                                </dd>
                            </div>
                        </dl>
                    </div>
                </div>
                <Button
                    v-if="hasHideableFields(entry)"
                    class="edit-history-fields-toggle"
                    variant="link"
                    size="small"
                    :label="fieldsToggleLabel(entry)"
                    @click="toggleAllFields(entry)"
                />
            </li>
        </ol>
        <Button
            v-if="nextCursor !== null"
            variant="link"
            size="small"
            :label="$gettext('Load more')"
            :loading="isLoading"
            @click="loadMore"
        />
    </div>
</template>

<style scoped>
.edit-history {
    display: flex;
    flex-direction: column;
    gap: 1.2rem;
    padding: 1.6rem;
    container-type: inline-size;
}

.edit-history-filter {
    inline-size: 100%;
}

.edit-history-filter-clear {
    inline-size: auto;
    block-size: auto;
    padding: 0;
    border: none;
    background: none;
    color: inherit;
    font-size: inherit;
}

.edit-history-filter-clear :deep(.p-button-icon) {
    font-size: inherit;
}

.edit-history-filter-clear:not(:disabled):hover {
    border: none;
    background: none;
    color: var(--p-text-color);
}

.edit-history-filter-clear:focus-visible {
    outline: 0.2rem solid var(--p-primary-color);
    outline-offset: 0.2rem;
    border-radius: 0.2rem;
}

.edit-history-empty {
    margin: 0;
    color: var(--p-text-muted-color);
    font-style: italic;
}

.edit-history-entries {
    display: flex;
    flex-direction: column;
    gap: 1.2rem;
    margin: 0;
    padding: 0;
    list-style: none;
}

.edit-history-entry {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
    padding: 1.2rem;
    border: 0.1rem solid var(--p-content-border-color);
    border-radius: var(--p-content-border-radius);
}

.edit-history-meta {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.8rem;
}

.edit-history-card {
    font-weight: 600;
}

.edit-history-user {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    color: var(--p-text-muted-color);
}

.edit-history-time {
    color: var(--p-text-muted-color);
    font-size: 1.2rem;
}

.edit-history-diff {
    display: flex;
    flex-direction: column;
    gap: 0.8rem;
}

.edit-history-state {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    padding: 0.8rem;
    border-radius: var(--p-content-border-radius);
    background: var(--p-content-hover-background);
}

.edit-history-state-label {
    color: var(--p-text-muted-color);
    font-size: 1.1rem;
    font-weight: 700;
    letter-spacing: 0.08rem;
    text-transform: uppercase;
}

.edit-history-fields {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
    margin: 0;
}

.edit-history-field {
    display: flex;
    gap: 0.6rem;
}

.edit-history-field dt {
    color: var(--p-text-muted-color);
    font-weight: 400;
}

.edit-history-field dd {
    display: inline-flex;
    align-items: baseline;
    gap: 0.4rem;
    margin: 0;
}

.edit-history-field-changed dd {
    color: var(--p-primary-color);
    font-weight: 600;
}

.edit-history-changed-marker {
    font-size: 1.1rem;
}

.edit-history-fields-toggle {
    align-self: flex-start;
    padding-inline: 0;
}

.edit-history-sr-only {
    position: absolute;
    inline-size: 0.1rem;
    block-size: 0.1rem;
    overflow: hidden;
    clip-path: inset(50%);
    white-space: nowrap;
}

@container (min-inline-size: 60rem) {
    .edit-history-diff {
        display: grid;
        grid-template-columns: 1fr 1fr;
    }
}
</style>
