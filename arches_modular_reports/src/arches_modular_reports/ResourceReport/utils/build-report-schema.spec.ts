import { describe, expect, it } from "vitest";

import { buildReportSchema } from "@/arches_modular_reports/ResourceReport/utils/build-report-schema.ts";

import type {
    NodePresentation,
    NodePresentationLookup,
} from "@/arches_modular_reports/ModularReport/types.ts";

function makeNodePresentation(
    overrides: Partial<NodePresentation> & {
        nodegroupAlias: string;
        nodegroupId: string;
        parentNodegroupId?: string | null;
    },
): NodePresentation {
    const { nodegroupAlias, nodegroupId, parentNodegroupId, ...rest } =
        overrides;
    return {
        nodeid: `${nodegroupId}-node`,
        name: "node",
        datatype: "string",
        card_name: nodegroupAlias,
        card_order: 0,
        card_visible: true,
        widget_label: "Label",
        widget_order: 0,
        visible: true,
        nodegroup: {
            nodegroup_id: nodegroupId,
            cardinality: "n",
            alias: nodegroupAlias,
            parent_nodegroup_id: parentNodegroupId ?? null,
            writable: true,
        },
        is_rich_text: false,
        is_numeric: false,
        is_required: false,
        number_format: { format: "", prefix: {}, suffix: {} },
        ...rest,
    };
}

const LOOKUP: NodePresentationLookup = {
    names: makeNodePresentation({
        nodegroupAlias: "names",
        nodegroupId: "ng-names",
        datatype: "semantic",
        card_order: 2,
    }),
    name_content: makeNodePresentation({
        nodegroupAlias: "names",
        nodegroupId: "ng-names",
        widget_order: 1,
    }),
    name_type: makeNodePresentation({
        nodegroupAlias: "names",
        nodegroupId: "ng-names",
        datatype: "concept",
        widget_order: 0,
    }),
    hidden_note: makeNodePresentation({
        nodegroupAlias: "names",
        nodegroupId: "ng-names",
        visible: false,
    }),
    production: makeNodePresentation({
        nodegroupAlias: "production",
        nodegroupId: "ng-production",
        datatype: "semantic",
        card_order: 1,
    }),
    production_location: makeNodePresentation({
        nodegroupAlias: "production_location",
        nodegroupId: "ng-production-location",
        parentNodegroupId: "ng-production",
        datatype: "semantic",
        card_order: 5,
    }),
    production_timespan: makeNodePresentation({
        nodegroupAlias: "production_timespan",
        nodegroupId: "ng-production-timespan",
        parentNodegroupId: "ng-production",
        datatype: "semantic",
        card_order: 3,
    }),
    hidden_card: makeNodePresentation({
        nodegroupAlias: "hidden_card",
        nodegroupId: "ng-hidden",
        datatype: "semantic",
        card_visible: false,
    }),
};

describe("buildReportSchema", () => {
    const schema = buildReportSchema(LOOKUP);

    it("orders visible top-level nodegroups by card order", () => {
        expect(schema.topLevelNodegroupAliases).toEqual([
            "production",
            "names",
        ]);
    });

    it("keeps only visible, non-semantic nodes, ordered by widget order", () => {
        expect(
            schema.nodegroupsByAlias.names.nodes.map((node) => node.alias),
        ).toEqual(["name_type", "name_content"]);
    });

    it("nests child nodegroups under their parent in card order", () => {
        expect(schema.nodegroupsByAlias.production.childAliases).toEqual([
            "production_timespan",
            "production_location",
        ]);
    });

    it("indexes every node by alias, including semantic ones", () => {
        expect(schema.nodesByAlias.production.alias).toBe("production");
        expect(schema.nodesByAlias.hidden_note.visible).toBe(false);
    });
});
