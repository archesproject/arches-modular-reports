export interface Settings {
    ACTIVE_LANGUAGE: string;
    ACTIVE_LANGUAGE_DIRECTION: string;
}

export interface NamedSection {
    name: string;
    content: SectionContent[];
}

export interface SectionContent {
    component: string;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    config: { [key: string]: any };
}

export interface NodePresentationLookup {
    [key: string]: {
        nodeid: string;
        name: string;
        widget_label: string;
        datatype: string;
    };
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type SingleTileValue = any;
export type TileValue = SingleTileValue | SingleTileValue[];
export interface Tile {
    [key: string]: TileValue;
}
