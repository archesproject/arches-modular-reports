import type { NodegroupWidgetConfig } from "@/arches_vue_components/types.ts";
import type { ResourceData } from "@/arches_modular_reports/ModularReport/types.ts";

export type LocalizedLabel = string | Record<string, string>;

export type ExportFormat = "json-ld" | "json" | "csv";

export type TagSeverity =
    | "info"
    | "success"
    | "warn"
    | "danger"
    | "secondary"
    | "contrast";

export interface SummaryEntryConfig {
    node_alias: string;
    label?: LocalizedLabel | null;
}

export interface HeaderConfig {
    summary?: SummaryEntryConfig[];
    export_formats?: ExportFormat[];
    lifecycle_severities?: Record<string, TagSeverity>;
}

export interface FolioConfig {
    nodegroup_alias: string;
}

export interface SectionConfig {
    label?: LocalizedLabel;
    icon?: string;
    folios?: FolioConfig[];
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

export interface HomeConfig {
    summary?: SummaryEntryConfig[];
    drawer?: DrawerPanelConfig[];
}

export interface ReportWorkspaceConfig {
    tabs?: TabConfig[];
    home?: HomeConfig;
}

export interface WorkspaceConfig {
    id: string;
    label?: LocalizedLabel;
    description?: LocalizedLabel;
    component: string;
    config?: ReportWorkspaceConfig;
}

export interface ResourceReportConfig {
    header?: HeaderConfig;
    workspaces?: WorkspaceConfig[];
}

export interface ResolvedWorkspace {
    id: string;
    label: string;
    description: string;
    component: string;
    config: ReportWorkspaceConfig;
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

export interface GraphNode {
    label: string;
    nodegroupAlias: string;
}

export interface SummaryLine {
    label: string;
    value: string;
}

export interface ReportData {
    resource: ResourceData;
    nodegroupWidgetConfigs: Record<string, NodegroupWidgetConfig>;
    graphNodesByAlias: Record<string, GraphNode>;
    context: ReportContext;
}
