import { describe, expect, it } from "vitest";

import {
    applyResourceChanges,
    replayResourceChanges,
} from "@/arches_modular_reports/ResourceReport/utils/resource-change-set.ts";
import { nodegroupTiles } from "@/arches_modular_reports/ResourceReport/utils/tiles.ts";

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
            makeTile("smalt", 0, {
                name_content: nodeData("Smalt"),
                name_notes: [],
            }),
            makeTile("cobalt", 1, {
                name_content: nodeData("Cobalt"),
                name_notes: [],
            }),
        ],
        description: makeTile("description", 0, {
            description_content: nodeData("Blue"),
        }),
    },
};

describe("resource change set replay", () => {
    it("applies adds, edits and reorders while sharing untouched nodegroups", () => {
        const workingResource = applyResourceChanges(RESOURCE, [
            {
                id: "edit",
                type: "edit",
                nodegroupAlias: "names",
                tileId: "smalt",
                aliasedData: { name_content: nodeData("Smalt blue") },
            },
            {
                id: "add",
                type: "add",
                nodegroupAlias: "name_notes",
                parentTileId: "cobalt",
                tile: makeTile("note", 0, { note_content: nodeData("Glass") }),
            },
            {
                id: "reorder",
                type: "reorder",
                nodegroupAlias: "names",
                parentTileId: null,
                tileIds: ["cobalt", "smalt"],
            },
        ]);

        const names = nodegroupTiles(workingResource.aliased_data.names);
        expect(names.map((tile) => tile.tileid)).toEqual(["cobalt", "smalt"]);
        expect(names[1].aliased_data.name_content).toEqual(
            nodeData("Smalt blue"),
        );
        expect(
            nodegroupTiles(names[0].aliased_data.name_notes).map(
                (tile) => tile.tileid,
            ),
        ).toEqual(["note"]);
        expect(workingResource.aliased_data.description).toBe(
            RESOURCE.aliased_data.description,
        );
    });

    it("removes deleted tiles and reports changes whose tiles have vanished", () => {
        const { resource, conflictingChanges } = replayResourceChanges(
            RESOURCE,
            [
                {
                    id: "delete",
                    type: "delete",
                    nodegroupAlias: "names",
                    tileId: "smalt",
                },
                {
                    id: "stale",
                    type: "edit",
                    nodegroupAlias: "names",
                    tileId: "removed-elsewhere",
                    aliasedData: {},
                },
            ],
        );

        expect(
            nodegroupTiles(resource.aliased_data.names).map(
                (tile) => tile.tileid,
            ),
        ).toEqual(["cobalt"]);
        expect(conflictingChanges.map((change) => change.id)).toEqual([
            "stale",
        ]);
    });
});
