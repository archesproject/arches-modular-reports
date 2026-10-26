import { computed, inject } from "vue";

import type { ComputedRef, InjectionKey } from "vue";
import type { ReportData } from "@/arches_modular_reports/ResourceReport/types.ts";

export const REPORT_DATA_KEY: InjectionKey<ComputedRef<ReportData | null>> =
    Symbol("reportData");

export function useReportData(): ComputedRef<ReportData> {
    const reportData = inject(REPORT_DATA_KEY);
    if (reportData === undefined) {
        throw new Error(
            "Report components must render inside a ResourceReport.",
        );
    }
    return computed(() => {
        if (reportData.value === null) {
            throw new Error("Report components render once the report loads.");
        }
        return reportData.value;
    });
}
