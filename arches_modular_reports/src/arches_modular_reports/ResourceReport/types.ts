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
    label: LocalizedLabel;
}

export interface ComponentNode<TConfig = Record<string, unknown>> {
    component: string;
    config: TConfig;
}

export interface LabelledConfig {
    label?: LocalizedLabel | null;
    description?: LocalizedLabel | null;
    icon?: string | null;
    requires_edit?: boolean;
}

export interface ContainerConfig {
    components?: ComponentNode[];
}

export type ResourceReportConfig = ContainerConfig;

export interface ReportHeaderConfig {
    summary?: SummaryEntryConfig[];
    export_formats?: ExportFormat[];
    lifecycle_severities?: Record<string, TagSeverity>;
}

export interface WorkspaceTabsConfig {
    banner?: ComponentNode[];
    components?: ComponentNode<LabelledConfig>[];
}

export interface ReportTabsConfig {
    components?: ComponentNode<LabelledConfig>[];
}

export interface SplitPaneConfig extends LabelledConfig {
    main?: ComponentNode[];
    aside?: ComponentNode[];
}

export interface StackConfig extends LabelledConfig, ContainerConfig {}

export interface SectionConfig extends LabelledConfig, ContainerConfig {}

export interface FolioConfig {
    nodegroup_alias?: string;
}

export interface DrawerConfig extends ContainerConfig {
    panels?: ComponentNode<LabelledConfig>[];
}

export interface KeyDataSummaryConfig {
    summary?: SummaryEntryConfig[];
}

export interface PlaceholderConfig extends LabelledConfig {
    message?: LocalizedLabel | null;
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

export interface HighlightSegment {
    text: string;
    matched: boolean;
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
    workingResource: ComputedRef<AliasedResourceData | null>;
    pendingChanges: ShallowRef<ResourceChange[]>;
    conflictingChangeIds: Ref<string[]>;
    fetchError: Ref<Error | null>;
    isSaving: Ref<boolean>;
    isBusy: ComputedRef<boolean>;
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
    isAvailable: boolean;
    open: (target: EditTileRequest) => void;
    close: () => void;
    register: () => () => void;
}

export interface ReportLifecycle {
    isTransitioning: boolean;
    transitionError: Error | null;
    transition: (lifecycleStateId: string) => Promise<void>;
}

export interface FolioRevealer {
    contains: (nodegroupAlias: string) => boolean;
    reveal: (nodegroupAlias: string) => void;
}

export interface FolioNavigation {
    flashedNodegroupAlias: Ref<string | null>;
    registerFolio: (nodegroupAlias: string, element: HTMLElement) => () => void;
    registerRevealer: (revealer: FolioRevealer) => () => void;
    jumpToNode: (nodeAlias: string) => Promise<void>;
    clearFlash: () => void;
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
    lifecycle: ReportLifecycle;
    folioNavigation: FolioNavigation;
}

export interface EditHistoryValue {
    node_alias: string;
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
    next_cursor: string | null;
}

export interface RelatedResourceItem {
    resourcexid: string;
    display_name: string;
    relationship: string;
    report_url: string;
}

export interface RelatedResourceGroup {
    graph_slug: string;
    graph_name: string;
    iconclass: string | null;
    color: string | null;
    next_cursor: string | null;
    items: RelatedResourceItem[];
}

export interface RelatedResourcesPanelConfig extends LabelledConfig {
    graphs?: string[];
}

export interface ImageSource {
    model: string;
    node: string;
}

export interface ImagesPanelConfig extends LabelledConfig {
    images?: ImageSource[];
}

export interface ResourceImagesPage {
    images: ResourceImage[];
    next_cursor: string | null;
}

export interface ResourceImage {
    url: string;
    caption: string;
    alt_text: string;
    resourceinstanceid: string;
    resource_name: string;
    report_url: string;
}
