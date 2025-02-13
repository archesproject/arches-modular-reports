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
    nodegroup: {
        nodegroup_id: string;
        cardinality: string;
    };
}

export interface NodePresentationLookup {
    [key: string]: NodePresentation;
}

export interface ComponentLookup {
    [key: string]: Component;
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

export interface LabelBasedTile {
    "@children": LabelBasedTile[];
    [key: string]: LabelBasedTile[] | LabelBasedNode;
}

export interface LabelBasedCard {
    "@has_children": boolean;
    "@node_id": string;
    "@tile_id": string;
    [key: string]: boolean | string | LabelBasedNode;
}

export interface LabelBasedNode {
    "@display_value": string;
    "@node_id": string;
    "@tile_id": string;
    instance_details?: ResourceDetails[];
    concept_details?: ConceptDetails[];
    url?: string;
    url_label?: string;
    [key: string]:
        | string
        | ResourceDetails[]
        | ConceptDetails[]
        | null
        | undefined;
}
