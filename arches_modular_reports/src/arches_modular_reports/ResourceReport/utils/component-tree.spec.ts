import { describe, expect, it } from "vitest";

import {
    componentPaths,
    folioLocations,
    nodegroupAliasesWithin,
} from "@/arches_modular_reports/ResourceReport/utils/component-tree.ts";

import type { ComponentNode } from "@/arches_modular_reports/ResourceReport/types.ts";

const REPORT_TREE: ComponentNode[] = [
    {
        component: "app/ReportTabs",
        config: {
            components: [
                {
                    component: "app/ReportStack",
                    config: {
                        label: { en: "Overview", de: "Übersicht" },
                        components: [
                            {
                                component: "app/ReportSection",
                                config: {
                                    label: "Names",
                                    components: [
                                        {
                                            component: "app/ReportFolio",
                                            config: {
                                                nodegroup_alias: "names",
                                            },
                                        },
                                    ],
                                },
                            },
                            {
                                component: "app/ReportFolio",
                                config: { nodegroup_alias: "statements" },
                            },
                        ],
                    },
                },
            ],
        },
    },
    {
        component: "app/ReportDrawer",
        config: {
            panels: [
                {
                    component: "app/ImagesPanel",
                    config: { images: [{ model: "photos", node: "file" }] },
                },
            ],
        },
    },
];

describe("componentPaths", () => {
    it("lists every component in the tree once", () => {
        expect(componentPaths(REPORT_TREE)).toEqual([
            "app/ReportTabs",
            "app/ReportStack",
            "app/ReportSection",
            "app/ReportFolio",
            "app/ReportDrawer",
            "app/ImagesPanel",
        ]);
    });
});

describe("nodegroupAliasesWithin", () => {
    it("collects the nodegroups a subtree shows", () => {
        expect([...nodegroupAliasesWithin(REPORT_TREE[0])]).toEqual([
            "names",
            "statements",
        ]);
        expect(nodegroupAliasesWithin(REPORT_TREE[1]).size).toBe(0);
    });
});

describe("folioLocations", () => {
    it("joins the labels above each folio in the active language", () => {
        expect(folioLocations(REPORT_TREE, "de")).toEqual({
            names: "Übersicht / Names",
            statements: "Übersicht",
        });
    });
});
