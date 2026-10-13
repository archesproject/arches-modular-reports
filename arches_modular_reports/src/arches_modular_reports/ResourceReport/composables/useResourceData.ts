import { ref, watchEffect } from "vue";

import { fetchModularReportResource } from "@/arches_modular_reports/ModularReport/api.ts";
import { toError } from "@/arches_modular_reports/utils.ts";

import type { Ref } from "vue";
import type { ResourceData } from "@/arches_modular_reports/ModularReport/types.ts";

export interface ResourceDataState {
    resource: Ref<ResourceData | null>;
    fetchError: Ref<Error | null>;
    reloadResource: () => Promise<void>;
}

export function useResourceData(
    graphSlug: string,
    resourceInstanceId: string,
): ResourceDataState {
    const resource = ref<ResourceData | null>(null);
    const fetchError = ref<Error | null>(null);

    async function reloadResource(): Promise<void> {
        try {
            resource.value = await fetchModularReportResource({
                graphSlug,
                resourceId: resourceInstanceId,
                fillBlanks: false,
            });
            fetchError.value = null;
        } catch (error) {
            fetchError.value = toError(error);
        }
    }

    watchEffect(reloadResource);

    return { resource, fetchError, reloadResource };
}
