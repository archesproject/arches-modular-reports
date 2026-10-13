import { ref, watchEffect } from "vue";

import { useNodegroupWidgetConfigStore } from "@/arches_vue_components/stores/useNodegroupWidgetConfigStore.ts";
import { toError } from "@/arches_modular_reports/utils.ts";

import type { Ref } from "vue";
import type { NodegroupWidgetConfig } from "@/arches_vue_components/types.ts";

export interface GraphWidgetConfigsState {
    nodegroupWidgetConfigs: Ref<Record<string, NodegroupWidgetConfig> | null>;
    fetchError: Ref<Error | null>;
}

export function useGraphWidgetConfigs(
    graphSlug: string,
): GraphWidgetConfigsState {
    const nodegroupWidgetConfigs = ref<Record<
        string,
        NodegroupWidgetConfig
    > | null>(null);
    const fetchError = ref<Error | null>(null);

    watchEffect(async () => {
        try {
            nodegroupWidgetConfigs.value =
                await useNodegroupWidgetConfigStore().fetchGraphWidgetConfigs(
                    graphSlug,
                );
        } catch (error) {
            fetchError.value = toError(error);
        }
    });

    return { nodegroupWidgetConfigs, fetchError };
}
