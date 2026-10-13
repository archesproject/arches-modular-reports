import { ref, watchEffect } from "vue";

import { fetchNodePresentation } from "@/arches_modular_reports/ModularReport/api.ts";
import { buildReportSchema } from "@/arches_modular_reports/ResourceReport/utils/build-report-schema.ts";
import { toError } from "@/arches_modular_reports/utils.ts";

import type { Ref } from "vue";
import type { ReportSchema } from "@/arches_modular_reports/ResourceReport/types.ts";

export interface ReportSchemaState {
    schema: Ref<ReportSchema | null>;
    fetchError: Ref<Error | null>;
}

export function useReportSchema(resourceInstanceId: string): ReportSchemaState {
    const schema = ref<ReportSchema | null>(null);
    const fetchError = ref<Error | null>(null);

    watchEffect(async () => {
        try {
            schema.value = buildReportSchema(
                await fetchNodePresentation(resourceInstanceId),
            );
        } catch (error) {
            fetchError.value = toError(error);
        }
    });

    return { schema, fetchError };
}
