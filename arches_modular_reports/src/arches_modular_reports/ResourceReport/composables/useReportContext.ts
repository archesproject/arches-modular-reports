import { ref, watchEffect } from "vue";

import {
    fetchReportContext,
    updateLifecycleState,
} from "@/arches_modular_reports/ResourceReport/api.ts";

import type { Ref } from "vue";
import type { ReportContext } from "@/arches_modular_reports/ResourceReport/types.ts";

export interface ReportContextState {
    context: Ref<ReportContext | null>;
    fetchError: Ref<Error | null>;
    isTransitioning: Ref<boolean>;
    transitionError: Ref<Error | null>;
    transitionLifecycle: (lifecycleStateId: string) => Promise<void>;
}

export function useReportContext(
    resourceInstanceId: string,
): ReportContextState {
    const context = ref<ReportContext | null>(null);
    const fetchError = ref<Error | null>(null);
    const isTransitioning = ref(false);
    const transitionError = ref<Error | null>(null);

    async function reloadContext(): Promise<void> {
        try {
            context.value = await fetchReportContext(resourceInstanceId);
            fetchError.value = null;
        } catch (error) {
            fetchError.value = error as Error;
        }
    }

    async function transitionLifecycle(
        lifecycleStateId: string,
    ): Promise<void> {
        isTransitioning.value = true;
        transitionError.value = null;
        try {
            await updateLifecycleState(resourceInstanceId, lifecycleStateId);
            await reloadContext();
        } catch (error) {
            transitionError.value = error as Error;
        } finally {
            isTransitioning.value = false;
        }
    }

    watchEffect(reloadContext);

    return {
        context,
        fetchError,
        isTransitioning,
        transitionError,
        transitionLifecycle,
    };
}
