<script setup lang="ts">
import { useGettext } from "vue3-gettext";

import type { ComponentTab } from "@/arches_modular_reports/ResourceReport/composables/useTabbedComponents.ts";

const { tab } = defineProps<{
    tab: ComponentTab;
}>();

const { $gettext } = useGettext();
</script>

<template>
    <span class="tab-label">
        <span>{{ tab.label }}</span>
        <template v-if="tab.hasData === false">
            <span
                class="tab-label-empty-marker"
                aria-hidden="true"
                :title="$gettext('No data recorded')"
            />
            <span class="tab-label-sr-only">
                {{ $gettext("(no data recorded)") }}
            </span>
        </template>
    </span>
</template>

<style scoped>
.tab-label {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
}

/* Hollow ring: flags a tab whose nodegroups have no values yet. */
.tab-label-empty-marker {
    flex-shrink: 0;
    inline-size: 0.7rem;
    block-size: 0.7rem;
    border: 0.15rem solid currentColor;
    border-radius: 50%;
}

.tab-label-sr-only {
    position: absolute;
    inline-size: 0.1rem;
    block-size: 0.1rem;
    overflow: hidden;
    clip-path: inset(50%);
    white-space: nowrap;
}
</style>
