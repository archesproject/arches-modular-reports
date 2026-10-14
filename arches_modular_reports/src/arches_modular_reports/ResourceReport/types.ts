import type { ComputedRef, Ref, ShallowRef } from "vue";
import type {
    AliasedData,
    AliasedNodeData,
    AliasedTileData,
    NodegroupWidgetConfig,
} from "@/arches_vue_components/types.ts";

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
}

export interface ReportGraph {
    name: string;
    slug: string;
    iconclass: string | null;
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

export interface SummaryRow {
    nodeAlias: string;
    label: string;
    values: string[];
}

export interface AliasedResourceData {
    resourceinstanceid: string;
    name?: string;
    aliased_data: AliasedData;
}

export interface AddTileChange {
    id: string;
    type: "add";
    nodegroupAlias: string;
    parentTileId: string | null;
    tile: AliasedTileData & { tileid: string };
}

export interface EditTileChange {
    id: string;
    type: "edit";
    nodegroupAlias: string;
    tileId: string;
    aliasedData: Record<string, AliasedNodeData>;
}

export interface DeleteTileChange {
    id: string;
    type: "delete";
    nodegroupAlias: string;
    tileId: string;
}

export interface ReorderTilesChange {
    id: string;
    type: "reorder";
    nodegroupAlias: string;
    parentTileId: string | null;
    tileIds: string[];
}

export type ResourceChange =
    | AddTileChange
    | EditTileChange
    | DeleteTileChange
    | ReorderTilesChange;

export type TileChangeType = "add" | "edit" | "delete";

export interface ResourceChangeSet {
    resource: ShallowRef<AliasedResourceData | null>;
    workingResource: ComputedRef<AliasedResourceData | null>;
    pendingChanges: ShallowRef<ResourceChange[]>;
    conflictingChangeIds: Ref<string[]>;
    fetchError: Ref<Error | null>;
    isSaving: Ref<boolean>;
    saveError: Ref<Error | null>;
    addError: Ref<Error | null>;
    addTile: (
        nodegroupAlias: string,
        parentTileId: string | null,
    ) => Promise<string | null>;
    editTile: (
        nodegroupAlias: string,
        tileId: string,
        aliasedData: AliasedData,
    ) => void;
    deleteTile: (nodegroupAlias: string, tileId: string) => void;
    undoDelete: (tileId: string) => void;
    reorderTiles: (
        nodegroupAlias: string,
        parentTileId: string | null,
        orderedTileIds: string[],
    ) => void;
    discardChange: (changeId: string) => void;
    discardAll: () => void;
    hasChanges: (change: ResourceChange) => boolean;
    changeTypeForTile: (tileId: string) => TileChangeType | null;
    isPendingDelete: (tileId: string) => boolean;
    save: () => Promise<boolean>;
}

export interface EditTileRequest {
    nodegroupAlias: string;
    tileId: string;
    nodeAlias?: string | null;
}

export interface ReportEditor {
    target: EditTileRequest | null;
    open: (target: EditTileRequest) => void;
    close: () => void;
}

export interface ReportData {
    resource: AliasedResourceData;
    nodegroupWidgetConfigs: Record<string, NodegroupWidgetConfig>;
    graphNodesByAlias: Record<string, GraphNode>;
    folioLocations: Record<string, string>;
    context: ReportContext;
    canEdit: boolean;
    changeSet: ResourceChangeSet;
    editor: ReportEditor;
}

export interface EditHistoryValue {
    node_alias: string;
    label: string;
    before: string | null;
    after: string | null;
    changed: boolean;
}

export interface EditHistoryEntry {
    editlogid: string;
    edit_type: string;
    timestamp: string;
    user: string;
    card_name: string | null;
    values: EditHistoryValue[];
}

export interface EditHistoryPage {
    results: EditHistoryEntry[];
    page: number;
    total_count: number;
    has_next: boolean;
}
