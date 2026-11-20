import { describe, expect, it } from "vitest";

import { tileHasData } from "@/arches_modular_reports/ResourceReport/utils/tiles.ts";

import type {
    AliasedData,
    AliasedNodeData,
    AliasedTileData,
} from "@/arches_vue_components/types.ts";
import type { NodeTextContext } from "@/arches_modular_reports/ResourceReport/types.ts";

const NODE_TEXT_CONTEXT: NodeTextContext = {
    richTextNodeAliases: new Set(),
    activeLanguage: "",
    defaultLanguage: "",
};

function nodeData(displayValue: string): AliasedNodeData {
    return {
        display_value: displayValue,
        node_value: displayValue === "" ? null : displayValue,
        details: [],
    };
}

function tile(tileid: string, aliasedData: AliasedData): AliasedTileData {
    return {
        aliased_data: aliasedData,
        nodegroup: tileid,
        parenttile: null,
        provisionaledits: null,
        resourceinstance: "resource",
        sortorder: 0,
        tileid,
    };
}

describe("tileHasData", () => {
    it("is true when a blank parent tile has a populated child tile", () => {
        const child = tile("part", { part_content: nodeData("Cobalt") });
        expect(
            tileHasData(
                tile("name", {
                    name_content: nodeData(""),
                    name_parts: [tile("empty-part", {}), child],
                }),
                NODE_TEXT_CONTEXT,
            ),
        ).toBe(true);
    });
});
