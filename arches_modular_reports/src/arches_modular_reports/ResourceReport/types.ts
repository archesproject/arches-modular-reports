import type { NodePresentation } from "@/arches_modular_reports/ModularReport/types.ts";

export type LocalizedLabel = string | Record<string, string>;

export type ExportFormat = "json-ld" | "json" | "csv";

export type TagSeverity =
    | "info"
    | "success"
    | "warn"
    | "danger"
    | "secondary"
    | "contrast";

export type DisplayMode = "cards" | "accordion" | "table";

export interface SummaryEntryConfig {
    node_alias: string;
    label?: LocalizedLabel;
}

export interface HeaderConfig {
    summary?: SummaryEntryConfig[];
    export_formats?: ExportFormat[];
    lifecycle_severities?: Record<string, TagSeverity>;
}

export interface CardConfig {
    nodegroup_alias: string;
    component?: string;
    label?: LocalizedLabel;
    labels?: Record<string, LocalizedLabel>;
    display?: DisplayMode;
    page_size?: number;
    primary_field?: string;
    row_fields?: string[];
    hide_row_field_labels?: boolean;
    single_line_fields?: boolean;
    badge_field?: string;
    geometry_alias?: string;
    children?: CardConfig[];
}

export interface SectionConfig {
    label?: LocalizedLabel;
    icon?: string;
    cards?: CardConfig[];
}

export interface TabConfig {
    label?: LocalizedLabel;
    sections?: SectionConfig[];
}

export interface DrawerPanelConfig {
    component: string;
    label?: LocalizedLabel;
    icon?: string;
    config?: Record<string, unknown>;
}

export type DrawerEntryConfig = string | DrawerPanelConfig;

export interface HomeConfig {
    summary?: SummaryEntryConfig[];
    drawer?: DrawerEntryConfig[];
}

export interface ReportViewConfig {
    tabs?: TabConfig[];
    home?: HomeConfig;
}

export interface ViewConfig {
    id: string;
    label?: LocalizedLabel;
    description?: LocalizedLabel;
    component: string;
    config?: ReportViewConfig;
}

export interface ResourceReportConfig {
    header?: HeaderConfig;
    views?: ViewConfig[];
}

export type ViewLayout = "report" | "data" | "full";

export interface ResolvedView {
    id: string;
    label: string;
    description: string;
    component: string;
    config: ReportViewConfig;
    layout: ViewLayout;
}

export interface LifecycleStateSummary {
    id: string;
    name: string;
    action_label: string;
    is_initial_state: boolean;
    can_edit_resource_instances: boolean;
    can_delete_resource_instances: boolean;
}

export interface LifecycleState extends LifecycleStateSummary {
    next_resource_instance_lifecycle_states: LifecycleStateSummary[];
    previous_resource_instance_lifecycle_states: LifecycleStateSummary[];
}

export interface ReportPermissions {
    can_edit: boolean;
    can_delete: boolean;
    can_copy: boolean;
    is_reviewer: boolean;
    is_rdm_admin: boolean;
}

export interface ReportGraph {
    name: string;
    slug: string;
    iconclass: string | null;
    color: string | null;
}

export interface ReportContext {
    graph: ReportGraph;
    lifecycle_state: LifecycleState;
    language: string;
    language_dir: "ltr" | "rtl";
    permissions: ReportPermissions;
}

export interface SchemaNode extends NodePresentation {
    alias: string;
}

export interface SchemaNodegroup {
    alias: string;
    nodegroupId: string;
    parentNodegroupId: string | null;
    cardinality: string;
    cardName: string;
    cardOrder: number;
    cardVisible: boolean;
    writable: boolean;
    nodes: SchemaNode[];
    childAliases: string[];
}

export interface ReportSchema {
    nodesByAlias: Record<string, SchemaNode>;
    nodegroupsByAlias: Record<string, SchemaNodegroup>;
    topLevelNodegroupAliases: string[];
}

export interface SummaryLine {
    label: string;
    value: string;
}
