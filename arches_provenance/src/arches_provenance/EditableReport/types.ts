import type { Component } from "vue";

export interface Settings {
    ACTIVE_LANGUAGE: string;
    ACTIVE_LANGUAGE_DIRECTION: string;
}

export interface NamedSection {
    name: string;
    components: SectionContent[];
}

export interface CollapableSection extends NamedSection {
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
    datatype: string;
}

export interface NodePresentationLookup {
    [key: string]: NodePresentation;
}

export interface ComponentLookup {
    [key: string]: Component;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type SingleTileValue = any;
export type TileValue = SingleTileValue | SingleTileValue[];
export interface Tile {
    [key: string]: TileValue;
}

export interface LabelBasedTile {
    "@children": LabelBasedTile[];
    [key: string]: LabelBasedTile[] | LabelBasedCard;
}

export interface LabelBasedCard {
    "@has_children": boolean;
    [key: string]: boolean | LabelBasedNode;
}

export interface LabelBasedNode {
    "@display_value": string;
    "@node_id": string;
    "@tile_id": string;
}
