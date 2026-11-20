<script setup lang="ts">
import { computed } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";

import {
    addResourceUrl,
    resourceManagerUrl,
    searchUrl,
} from "@/arches_modular_reports/ResourceReport/api.ts";

import type { ReportContext } from "@/arches_modular_reports/ResourceReport/types.ts";

const { resourceName, context } = defineProps<{
    resourceName: string;
    context: ReportContext;
}>();

const { $gettext } = useGettext();

const heading = computed(() => {
    if (resourceName) {
        return $gettext("“%{name}” was deleted", { name: resourceName }, true);
    }
    return $gettext(
        "This %{graphName} was deleted",
        { graphName: context.graph.name },
        true,
    );
});
</script>

<template>
    <div
        class="deleted-resource"
        :dir="context.language_dir"
    >
        <section
            class="deleted-resource-message"
            role="status"
        >
            <i
                class="pi pi-trash"
                aria-hidden="true"
            />
            <h2 class="deleted-resource-heading">{{ heading }}</h2>
            <p class="deleted-resource-detail">
                {{
                    $gettext(
                        "The record and its data have been removed. It no longer appears in search results or in other records' reports.",
                    )
                }}
            </p>
            <div class="deleted-resource-actions">
                <Button
                    v-if="context.permissions.can_create"
                    as="a"
                    icon="pi pi-plus"
                    size="small"
                    :href="addResourceUrl(context.graph.graphid)"
                    :label="
                        $gettext(
                            'Create a new %{graphName}',
                            { graphName: context.graph.name },
                            true,
                        )
                    "
                />
                <Button
                    as="a"
                    icon="pi pi-search"
                    variant="outlined"
                    size="small"
                    :href="searchUrl()"
                    :label="$gettext('Search')"
                />
                <Button
                    as="a"
                    icon="pi pi-list"
                    variant="outlined"
                    size="small"
                    :href="resourceManagerUrl()"
                    :label="$gettext('Go to the Resource Manager')"
                />
            </div>
        </section>
    </div>
</template>

<style scoped>
.deleted-resource {
    display: flex;
    justify-content: center;
    padding-block: 6.4rem 3.2rem;
    padding-inline: 2.4rem;
}

.deleted-resource-message {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
    inline-size: 100%;
    max-inline-size: 56rem;
    padding-block: 6.4rem;
    padding-inline: 2.4rem;
    border: 0.1rem solid var(--p-content-border-color);
    border-radius: 0.4rem;
    background: var(--p-content-hover-background);
    color: var(--p-text-muted-color);
    text-align: center;
}

.deleted-resource-message > i {
    font-size: 2.8rem;
    opacity: 0.35;
}

.deleted-resource-heading {
    margin: 0;
    color: var(--p-text-color);
    font-size: 1.8rem;
    font-weight: 600;
    line-height: 1.3;
}

.deleted-resource-detail {
    margin: 0;
    font-size: 1.4rem;
    line-height: 1.4;
}

.deleted-resource-actions {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 0.8rem;
    margin-block-start: 1.2rem;
}

.deleted-resource-actions :deep(.p-button) {
    border-radius: 0.15rem;
}
</style>
