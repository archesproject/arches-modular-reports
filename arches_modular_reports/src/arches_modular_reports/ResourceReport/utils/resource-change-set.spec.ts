import { describe, expect, it } from "vitest";

import {
    loadedNodeValues,
    rebaseChanges,
    withLoadedOriginals,
} from "@/arches_modular_reports/ResourceReport/utils/resource-change-set.ts";

import type {
    AliasedData,
    AliasedNodeData,
    AliasedTileData,
} from "@/arches_vue_components/types.ts";
import type { AliasedResourceData } from "@/arches_modular_reports/ResourceReport/types.ts";

function nodeData(value: string): AliasedNodeData {
    return { display_value: value, node_value: value, details: [] };
}

function makeTile(
    tileid: string,
    sortorder: number,
    aliasedData: AliasedData,
): AliasedTileData & { tileid: string } {
    return {
        aliased_data: aliasedData,
        nodegroup: "nodegroup",
        parenttile: null,
        provisionaledits: null,
        resourceinstance: "resource",
        sortorder,
        tileid,
    };
}

const RESOURCE: AliasedResourceData = {
    resourceinstanceid: "resource",
    aliased_data: {
        names: [
            makeTile("smalt", 0, { name_content: nodeData("Smalt") }),
            makeTile("cobalt", 1, { name_content: nodeData("Cobalt") }),
        ],
    },
};

describe("resource change set originals", () => {
    it("reads loaded node values, using null for missing nodes", () => {
        expect(
            loadedNodeValues(makeTile("smalt", 0, { a: nodeData("A") }), [
                "a",
                "b",
            ]),
        ).toEqual({ a: "A", b: null });
        expect(loadedNodeValues(null, ["a"])).toEqual({ a: null });
    });

    it("re-anchors an edit's originals to a fresh resource", () => {
        const change = withLoadedOriginals(
            {
                id: "edit",
                type: "edit",
                nodegroupAlias: "names",
                tileId: "smalt",
                aliasedData: { name_content: nodeData("Smalt blue") },
                original: { name_content: "stale" },
            },
            RESOURCE,
        );

        expect(change).toMatchObject({ original: { name_content: "Smalt" } });
    });

    it("turns an add of an existing tile into an edit with originals", () => {
        const [change] = rebaseChanges(
            [
                {
                    id: "add",
                    type: "add",
                    nodegroupAlias: "names",
                    parentTileId: null,
                    tile: makeTile("smalt", 0, {
                        name_content: nodeData("Smalt blue"),
                    }),
                },
            ],
            RESOURCE,
        );

        expect(change).toMatchObject({
            type: "edit",
            tileId: "smalt",
            original: { name_content: "Smalt" },
        });
    });

    it("drops nodes, and their originals, that match the resource", () => {
        const [change] = rebaseChanges(
            [
                {
                    id: "edit",
                    type: "edit",
                    nodegroupAlias: "names",
                    tileId: "smalt",
                    aliasedData: {
                        name_content: nodeData("Smalt"),
                        name_notes: nodeData("Glaze"),
                    },
                    original: { name_content: "Smalt", name_notes: null },
                },
            ],
            RESOURCE,
        );

        expect(change).toMatchObject({
            aliasedData: { name_notes: nodeData("Glaze") },
            original: { name_notes: null },
        });
        expect(Object.keys((change as { original: object }).original)).toEqual([
            "name_notes",
        ]);
    });
});
