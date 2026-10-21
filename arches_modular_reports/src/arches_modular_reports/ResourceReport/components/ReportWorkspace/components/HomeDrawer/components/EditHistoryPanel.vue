<script setup lang="ts">
import { computed, ref, watchEffect } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";
import IconField from "openvue/iconfield";
import InputIcon from "openvue/inputicon";
import InputText from "openvue/inputtext";
import Message from "openvue/message";
import Tag from "openvue/tag";

import { fetchEditHistory } from "@/arches_modular_reports/ResourceReport/api.ts";
import { useFilterQuery } from "@/arches_modular_reports/ResourceReport/composables/useFilterQuery.ts";
import { toError } from "@/arches_modular_reports/utils.ts";

import type {
    EditHistoryEntry,
    ReportData,
    TagSeverity,
} from "@/arches_modular_reports/ResourceReport/types.ts";

const TILE_CREATE = "tile create";
const TILE_EDIT = "tile edit";
const TILE_DELETE = "tile delete";

const { reportData } = defineProps<{
    reportData: ReportData;
    panelConfig: Record<string, unknown>;
}>();

const { $gettext } = useGettext();
const { filterText, query } = useFilterQuery();

const entries = ref<EditHistoryEntry[]>([]);
const currentPage = ref(1);
const hasNextPage = ref(false);
const isLoading = ref(false);
const loadError = ref<Error | null>(null);
let latestHistoryRequestNumber = 0;

const resourceInstanceId = computed(
    () => reportData.resource.resourceinstanceid,
);

watchEffect(() => {
    loadHistory(query.value, 1);
});

async function loadHistory(searchText: string, page: number): Promise<void> {
    latestHistoryRequestNumber += 1;
    const historyRequestNumber = latestHistoryRequestNumber;
    isLoading.value = true;
    loadError.value = null;
    try {
        const historyPage = await fetchEditHistory(
            resourceInstanceId.value,
            page,
            searchText,
        );
        if (historyRequestNumber !== latestHistoryRequestNumber) {
            return;
        }
        if (page === 1) {
            entries.value = historyPage.results;
        } else {
            entries.value = [...entries.value, ...historyPage.results];
        }
        currentPage.value = historyPage.page;
        hasNextPage.value = historyPage.has_next;
    } catch (error) {
        if (historyRequestNumber === latestHistoryRequestNumber) {
            loadError.value = toError(error);
        }
    } finally {
        if (historyRequestNumber === latestHistoryRequestNumber) {
            isLoading.value = false;
        }
    }
}

function loadMore(): void {
    loadHistory(query.value, currentPage.value + 1);
}

function editTypeLabel(entry: EditHistoryEntry): string {
    if (entry.edit_type === TILE_CREATE) {
        return $gettext("create");
    }
    if (entry.edit_type === TILE_EDIT) {
        return $gettext("update");
    }
    if (entry.edit_type === TILE_DELETE) {
        return $gettext("delete");
    }
    return entry.edit_type;
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
    return new Date(timestamp).toLocaleString(reportData.context.language);
}

function fieldLabel(nodeAlias: string): string {
    return reportData.graphNodesByAlias[nodeAlias].label;
}
</script>

<template>
    <div class="edit-history">
        <IconField>
            <InputIcon class="pi pi-search" />
            <InputText
                v-model="filterText"
                class="edit-history-filter"
                :placeholder="$gettext('Filter by card or user…')"
                :aria-label="$gettext('Filter the edit history')"
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
                        :value="editTypeLabel(entry)"
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
                                v-for="value in entry.values"
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
                                <dd>{{ value.before }}</dd>
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
                                v-for="value in entry.values"
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
                                <dd>{{ value.after }}</dd>
                            </div>
                        </dl>
                    </div>
                </div>
            </li>
        </ol>
        <Button
            v-if="hasNextPage"
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
}

.edit-history-filter {
    inline-size: 100%;
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
}

.edit-history-field dd {
    margin: 0;
}

.edit-history-field-changed dd {
    color: var(--p-primary-color);
    font-weight: 600;
}
</style>
