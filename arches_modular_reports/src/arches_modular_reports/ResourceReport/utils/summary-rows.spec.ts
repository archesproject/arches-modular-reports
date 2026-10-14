import { describe, expect, it } from "vitest";

import { summaryRows } from "@/arches_modular_reports/ResourceReport/utils/summary-rows.ts";

import type {
    AliasedNodeData,
    AliasedTileData,
} from "@/arches_vue_components/types.ts";
import type { GraphNode } from "@/arches_modular_reports/ResourceReport/types.ts";

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

const GRAPH_NODES_BY_ALIAS: Record<string, GraphNode> = {
    name_content: { label: "Name", nodegroupAlias: "names" },
};

describe("summaryRows", () => {
    it("labels each entry from its node and keeps its non-empty values in order", () => {
        expect(
            summaryRows(
                [{ node_alias: "name_content" }],
                ALIASED_DATA,
                GRAPH_NODES_BY_ALIAS,
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

    it("prefers a configured label in the active language", () => {
        const [summaryRow] = summaryRows(
            [
                {
                    node_alias: "name_content",
                    label: { en: "Pigment", de: "Pigment (de)" },
                },
            ],
            ALIASED_DATA,
            GRAPH_NODES_BY_ALIAS,
            "de",
        );

        expect(summaryRow.label).toBe("Pigment (de)");
    });
});
