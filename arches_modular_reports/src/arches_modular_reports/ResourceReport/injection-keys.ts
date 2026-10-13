import type { InjectionKey } from "vue";

import type { ReportContextState } from "@/arches_modular_reports/ResourceReport/composables/useReportContext.ts";
import type { ReportSchemaState } from "@/arches_modular_reports/ResourceReport/composables/useReportSchema.ts";
import type { ResourceDataState } from "@/arches_modular_reports/ResourceReport/composables/useResourceData.ts";

export const REPORT_CONTEXT_KEY: InjectionKey<ReportContextState> =
    Symbol("reportContext");
export const REPORT_SCHEMA_KEY: InjectionKey<ReportSchemaState> =
    Symbol("reportSchema");
export const RESOURCE_DATA_KEY: InjectionKey<ResourceDataState> =
    Symbol("resourceData");
