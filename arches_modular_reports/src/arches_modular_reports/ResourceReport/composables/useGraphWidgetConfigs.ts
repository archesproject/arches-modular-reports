import { ref, watchEffect } from "vue";

import { useNodegroupWidgetConfigStore } from "@/arches_vue_components/stores/useNodegroupWidgetConfigStore.ts";

import type { Ref } from "vue";
import type { NodegroupWidgetConfig } from "@/arches_vue_components/types.ts";

export interface GraphWidgetConfigsState {
    nodegroupWidgetConfigs: Ref<Record<string, NodegroupWidgetConfig> | null>;
    fetchError: Ref<Error | null>;
}

export function useGraphWidgetConfigs(
    graphSlug: string,
): GraphWidgetConfigsState {
    const nodegroupWidgetConfigStore = useNodegroupWidgetConfigStore();
    const nodegroupWidgetConfigs = ref<Record<
        string,
        NodegroupWidgetConfig
    > | null>(null);
    const fetchError = ref<Error | null>(null);

    watchEffect(async () => {
        try {
            nodegroupWidgetConfigs.value =
                await nodegroupWidgetConfigStore.fetchGraphWidgetConfigs(
                    graphSlug,
                );
        } catch (error) {
            fetchError.value = error as Error;
        }
    });

    return { nodegroupWidgetConfigs, fetchError };
}
