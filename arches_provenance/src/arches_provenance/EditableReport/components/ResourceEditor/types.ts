// eslint-disable-next-line
interface AliasedData {}

// We might end up defining this type in more detail.

export interface NodeValue {
    ["@display_value"]?: string;
    aliased_data?: AliasedData;
}

export interface TileData {
    tileid: string;
    resourceinstance: string;
    parenttile?: string | null;
    sortorder?: number | null;
    provisionaledits?: object | null;
    nodegroup?: string;
    aliased_data: AliasedData;
}

export interface ResourceData {
    resourceinstanceid: string;
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
    aliased_data: AliasedData;
}
