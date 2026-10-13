import type {
    ExportFormat,
    ViewConfig,
} from "@/arches_modular_reports/ResourceReport/types.ts";

export const REPORT_VIEW = "ReportView";
export const DATA_VIEW = "DataView";
export const GRAPH_VIEW = "GraphView";

export const DEFAULT_VIEW_CONFIGS: ViewConfig[] = [
    { id: "report", component: REPORT_VIEW },
    { id: "data", component: DATA_VIEW },
    { id: "graph", component: GRAPH_VIEW },
];

export const DEFAULT_EXPORT_FORMATS: ExportFormat[] = [
    "json-ld",
    "json",
    "csv",
];

export const EXPORT_FORMAT_LABELS: Record<ExportFormat, string> = {
    "json-ld": "JSON-LD",
    json: "JSON",
    csv: "CSV",
};

export const SEMANTIC_DATATYPE = "semantic";

export const EMPTY_VALUE = "—";
