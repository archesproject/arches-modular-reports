import { describe, expect, it } from "vitest";

import { findNodeValues } from "@/arches_modular_reports/ResourceReport/utils/find-node-values.ts";

import type { AliasedData } from "@/arches_vue_components/types.ts";

function makeTile(aliasedData: AliasedData) {
    return {
        aliased_data: aliasedData,
        nodegroup: "nodegroup",
        parenttile: null,
        provisionaledits: null,
        resourceinstance: "resource",
        sortorder: 0,
        tileid: "tile",
    };
}

const RESOURCE_ALIASED_DATA = {
    names: [
        makeTile({
            name_content: {
                display_value: "Cobalt blue",
                node_value: {},
                details: [],
            },
        }),
        makeTile({
            name_content: {
                display_value: "Pigment Blue 28",
                node_value: {},
                details: [],
            },
        }),
    ],
    production: makeTile({
        production_location: makeTile({
            location_note: {
                display_value: "Getty Center",
                node_value: "Getty Center",
                details: [],
            },
        }),
    }),
    empty_branch: null,
} satisfies AliasedData;

describe("findNodeValues", () => {
    it("collects values from every tile of a cardinality-n nodegroup", () => {
        expect(
            findNodeValues(RESOURCE_ALIASED_DATA, "name_content").map(
                (nodeData) => nodeData.display_value,
            ),
        ).toEqual(["Cobalt blue", "Pigment Blue 28"]);
    });

    it("finds values nested in child tiles", () => {
        expect(
            findNodeValues(RESOURCE_ALIASED_DATA, "location_note")[0]
                .display_value,
        ).toBe("Getty Center");
    });
});
