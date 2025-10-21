import type { Component } from "vue";

import type {
    AliasedNodeData,
    AliasedNodegroupData,
} from "@/arches_component_lab/types.ts";

export interface LanguageSettings {
    ACTIVE_LANGUAGE: string;
    ACTIVE_LANGUAGE_DIRECTION: string;
}

export interface NamedSection {
    name: string;
    components: SectionContent[];
}

export interface CollapsibleSection extends NamedSection {
    collapsed: boolean;
}

export interface SectionContent {
    component: string;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    config: { [key: string]: any };
}

export interface NodePresentation {
    nodeid: string;
    name: string;
    card_name: string;
    card_order: number;
    widget_label: string;
    widget_order: number;
    visible: boolean;
    nodegroup: {
        nodegroup_id: string;
        cardinality: string;
    };
    is_rich_text: boolean;
    is_numeric: boolean;
    number_format: NumberFormat;
}

export interface NodePresentationLookup {
    [key: string]: NodePresentation;
}

export interface KeyedComponent {
    component: Component;
    key: number;
}

export interface ComponentLookup {
    [key: string]: KeyedComponent;
}

export interface ResourceDetails {
    display_value: string;
    resource_id: string;
}

export interface ConceptDetails {
    concept_id: string;
    language_id: string;
    value: string;
    valueid: string;
    valuetype_id: string;
}

export interface URLDetails {
    url: string;
    url_label: string;
}

export interface ReferenceDetails {
    uri: string;
    display_value: string;
    list_item_id: string;
}

export interface NodeValueDisplayData {
    display_values: string[];
    links: {
        label: string;
        link: string;
    }[];
}

export interface NodeValueDisplayDataLookup {
    [key: string]: NodeValueDisplayData[];
}

export interface NodeData {
    display_value: string;
    node_value: unknown;
    details: unknown[];
}

export type NodegroupData = TileData | TileData[] | null;

export interface AliasedData {
    [key: string]: AliasedNodeData | AliasedNodegroupData;
}

export interface TileData {
    aliased_data: AliasedData;
    nodegroup: string;
    parenttile: string | null;
    provisionaledits: object | null;
    resourceinstance: string;
    sortorder: number;
    tileid: string | null;
}

export interface ResourceData {
    aliased_data: AliasedData;
    resourceinstanceid?: string;
    name?: string;
    descriptors?: {
        [key: string]: {
            name: string;
            map_popup: string;
            description: string;
        };
    };
    legacyid?: string | null;
    createdtime?: string;
    graph?: string;
    graph_publication: string;
    principaluser: number;
}

// NodegroupTileDataView produces this, not label-based graph.
export interface LabelBasedCard {
    "@has_children": boolean;
    "@tile_id": string;
    [key: string]: boolean | string | null;
}

export interface NumberFormat {
    format: string;
    prefix: Record<string, string>;
    suffix: Record<string, string>;
}
