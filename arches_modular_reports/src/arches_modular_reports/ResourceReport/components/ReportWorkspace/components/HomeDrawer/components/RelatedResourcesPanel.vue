<script setup lang="ts">
import { computed, ref, watchEffect } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";
import IconField from "openvue/iconfield";
import InputIcon from "openvue/inputicon";
import InputText from "openvue/inputtext";
import Message from "openvue/message";

import {
    fetchRelatedResourceGroup,
    fetchRelatedResourceGroups,
} from "@/arches_modular_reports/ResourceReport/api.ts";
import { useFilterQuery } from "@/arches_modular_reports/ResourceReport/composables/useFilterQuery.ts";
import { DEFAULT_GRAPH_ICON_CLASS } from "@/arches_modular_reports/ResourceReport/constants.ts";
import { toError } from "@/arches_modular_reports/utils.ts";

import type {
    RelatedResourceGroup,
    RelatedResourcesPanelConfig,
    ReportData,
} from "@/arches_modular_reports/ResourceReport/types.ts";

const { reportData, panelConfig } = defineProps<{
    reportData: ReportData;
    panelConfig: RelatedResourcesPanelConfig;
}>();

const { $gettext } = useGettext();
const { filterText, query } = useFilterQuery();

const groups = ref<RelatedResourceGroup[]>([]);
const loadingGraphSlug = ref<string | null>(null);
const loadError = ref<Error | null>(null);
let latestGroupsRequestNumber = 0;

const resourceInstanceId = computed(
    () => reportData.resource.resourceinstanceid,
);

watchEffect(() => {
    loadGroups(query.value);
});

async function loadGroups(searchText: string): Promise<void> {
    latestGroupsRequestNumber += 1;
    const groupsRequestNumber = latestGroupsRequestNumber;
    loadError.value = null;
    try {
        const loadedGroups = await fetchRelatedResourceGroups(
            resourceInstanceId.value,
            panelConfig.graphs ?? [],
            searchText,
        );
        if (groupsRequestNumber === latestGroupsRequestNumber) {
            groups.value = loadedGroups;
        }
    } catch (error) {
        if (groupsRequestNumber === latestGroupsRequestNumber) {
            loadError.value = toError(error);
        }
    }
}

async function loadMore(group: RelatedResourceGroup): Promise<void> {
    const groupsRequestNumber = latestGroupsRequestNumber;
    loadingGraphSlug.value = group.graph_slug;
    loadError.value = null;
    try {
        const nextPage = await fetchRelatedResourceGroup(
            resourceInstanceId.value,
            group.graph_slug,
            group.page + 1,
            query.value,
        );
        if (groupsRequestNumber !== latestGroupsRequestNumber) {
            return;
        }
        groups.value = groups.value.map((candidate) => {
            if (candidate.graph_slug !== group.graph_slug) {
                return candidate;
            }
            return {
                ...nextPage,
                items: [...candidate.items, ...nextPage.items],
            };
        });
    } catch (error) {
        if (groupsRequestNumber === latestGroupsRequestNumber) {
            loadError.value = toError(error);
        }
    } finally {
        if (loadingGraphSlug.value === group.graph_slug) {
            loadingGraphSlug.value = null;
        }
    }
}
</script>

<template>
    <div class="related-resources">
        <IconField>
            <InputIcon class="pi pi-search" />
            <InputText
                v-model="filterText"
                class="related-resources-filter"
                :placeholder="
                    $gettext('Filter by model, name, or relationship…')
                "
                :aria-label="$gettext('Filter the related resources')"
            />
        </IconField>
        <Message
            v-if="loadError"
            severity="error"
        >
            <span>
                {{
                    $gettext(
                        "Unable to load related resources: %{message}",
                        { message: loadError.message },
                        true,
                    )
                }}
            </span>
        </Message>
        <section
            v-for="group in groups"
            :key="group.graph_slug"
            class="related-resources-group"
        >
            <h4 class="related-resources-group-label">
                <i
                    aria-hidden="true"
                    :class="group.iconclass || DEFAULT_GRAPH_ICON_CLASS"
                    :style="{ color: group.color ?? undefined }"
                />
                <span>{{ group.graph_name }}</span>
            </h4>
            <p
                v-if="group.items.length === 0"
                class="related-resources-empty"
            >
                {{
                    $gettext(
                        "No related %{model}",
                        {
                            model: group.graph_name,
                        },
                        true,
                    )
                }}
            </p>
            <ul
                v-else
                class="related-resources-items"
            >
                <li
                    v-for="item in group.items"
                    :key="item.resourcexid"
                    class="related-resources-item"
                >
                    <Button
                        as="a"
                        variant="link"
                        size="small"
                        :href="item.report_url"
                        :label="item.display_name"
                    />
                    <span class="related-resources-relationship">
                        {{ item.relationship }}
                    </span>
                </li>
            </ul>
            <Button
                v-if="group.has_next"
                variant="link"
                size="small"
                :label="$gettext('Load more')"
                :loading="loadingGraphSlug === group.graph_slug"
                @click="loadMore(group)"
            />
        </section>
    </div>
</template>

<style scoped>
.related-resources {
    display: flex;
    flex-direction: column;
    gap: 1.6rem;
    padding: 1.6rem;
}

.related-resources-filter {
    inline-size: 100%;
}

.related-resources-group {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
}

.related-resources-group-label {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin: 0;
    color: var(--p-text-muted-color);
    font-size: 1.2rem;
    font-weight: 700;
    letter-spacing: 0.08rem;
    text-transform: uppercase;
}

.related-resources-empty {
    margin: 0;
    color: var(--p-text-muted-color);
    font-style: italic;
}

.related-resources-items {
    display: flex;
    flex-direction: column;
    margin: 0;
    padding: 0;
    list-style: none;
}

.related-resources-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1.2rem;
    padding-block: 0.6rem;
    border-block-end: 0.1rem solid var(--p-content-border-color);
}

.related-resources-relationship {
    color: var(--p-text-muted-color);
    font-size: 1.2rem;
    font-style: italic;
}
</style>
