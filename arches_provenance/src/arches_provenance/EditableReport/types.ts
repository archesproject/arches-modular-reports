import type { Component } from "vue";

export interface Settings {
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
    widget_label: string;
    visible: boolean;
    nodegroup: {
        nodegroup_id: string;
        cardinality: string;
    };
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
    inverseOntologyProperty: string;
    ontologyProperty: string;
    resourceId: string;
    resourceXresourceId: string;
}

export interface ConceptDetails {
    concept_id: string;
    language_id: string;
    value: string;
    valueid: string;
    valuetype_id: string;
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

// eslint-disable-next-line
interface AliasedData {}

export interface ResourceData<T extends AliasedData = AliasedData> {
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
    aliased_data: T;
}

export interface TileData<T extends AliasedData = AliasedData> {
    aliased_data: T;
    nodegroup: string;
    parenttile: string | null;
    provisionaledits: object | null;
    resourceinstance: string;
    sortorder: number;
    tileid: string;
}

// NodegroupTileDataView produces this, not label-based graph.
export interface LabelBasedCard {
    "@has_children": boolean;
    "@tile_id": string;
    [key: string]: boolean | string | null;
}
