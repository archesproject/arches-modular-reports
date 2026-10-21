import { describe, expect, it } from "vitest";

import { summaryRows } from "@/arches_modular_reports/ResourceReport/utils/summary-rows.ts";

import type {
    AliasedNodeData,
    AliasedTileData,
} from "@/arches_vue_components/types.ts";

function nameTile(
    tileid: string,
    sortorder: number,
    displayValue: string,
): AliasedTileData {
    const nameContent: AliasedNodeData = {
        display_value: displayValue,
        node_value: displayValue,
        details: [],
    };
    return {
        aliased_data: { name_content: nameContent },
        nodegroup: "names",
        parenttile: null,
        provisionaledits: null,
        resourceinstance: "resource",
        sortorder,
        tileid,
    };
}

const ALIASED_DATA = {
    names: [
        nameTile("cobalt", 2, "Cobalt"),
        nameTile("blank", 1, ""),
        nameTile("smalt", 0, "Smalt"),
    ],
};

describe("summaryRows", () => {
    it("labels each entry from its config and keeps its non-empty values in order", () => {
        expect(
            summaryRows(
                [{ node_alias: "name_content", label: { en: "Name" } }],
                ALIASED_DATA,
                "en",
            ),
        ).toEqual([
            {
                nodeAlias: "name_content",
                label: "Name",
                values: ["Smalt", "Cobalt"],
            },
        ]);
    });
});
