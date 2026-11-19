import { describe, expect, it } from "vitest";

import {
    containsFolios,
    folioLocations,
    nodegroupAliasesWithin,
    reportTabGroups,
    withoutHiddenCards,
} from "@/arches_modular_reports/ResourceReport/utils/component-tree.ts";

import type { NodegroupWidgetConfig } from "@/arches_vue_components/types.ts";
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

describe("nodegroupAliasesWithin", () => {
    it("collects the nodegroups a subtree shows", () => {
        expect([...nodegroupAliasesWithin(REPORT_TREE[0])]).toEqual([
            "names",
            "statements",
        ]);
        expect(nodegroupAliasesWithin(REPORT_TREE[1]).size).toBe(0);
    });
});

describe("reportTabGroups", () => {
    it("lists each report tab with the nodegroups it shows", () => {
        expect(reportTabGroups(REPORT_TREE, "de", "en")).toEqual([
            { label: "Übersicht", nodegroupAliases: ["names", "statements"] },
        ]);
    });

    it("places a nodegroup shown in two tabs in the first only", () => {
        const tab = (
            label: string,
            nodegroupAliases: string[],
        ): ComponentNode => ({
            component: "app/ReportStack",
            config: {
                label,
                components: nodegroupAliases.map((nodegroupAlias) => ({
                    component: "app/ReportFolio",
                    config: { nodegroup_alias: nodegroupAlias },
                })),
            },
        });
        const tree: ComponentNode[] = [
            {
                component: "app/ReportTabs",
                config: {
                    components: [
                        tab("Overview", ["names"]),
                        tab("Physical", ["names", "colors"]),
                    ],
                },
            },
        ];

        expect(reportTabGroups(tree, "en", "en")).toEqual([
            { label: "Overview", nodegroupAliases: ["names"] },
            { label: "Physical", nodegroupAliases: ["colors"] },
        ]);
    });

    it("finds no tabs in a report without ReportTabs", () => {
        expect(reportTabGroups([REPORT_TREE[1]], "en", "en")).toEqual([]);
    });
});

describe("folioLocations", () => {
    it("joins the labels above each folio in the active language", () => {
        expect(folioLocations(REPORT_TREE, "de", "en")).toEqual({
            names: "Übersicht / Names",
            statements: "Übersicht",
        });
    });
});

describe("containsFolios", () => {
    it("finds folios at any depth, and only folios", () => {
        expect(containsFolios(REPORT_TREE[0])).toBe(true);
        expect(
            containsFolios({
                component: "app/SplitPane",
                config: {
                    main: [
                        {
                            component: "app/DataBrowser/DataBrowser",
                            config: {},
                        },
                    ],
                },
            }),
        ).toBe(false);
    });
});

describe("withoutHiddenCards", () => {
    const configs = {
        names: { card: { visible: true } },
        statements: { card: { visible: false } },
    } as unknown as Record<string, NodegroupWidgetConfig>;

    function folio(nodegroupAlias: string): ComponentNode {
        return {
            component: "app/ReportFolio",
            config: { nodegroup_alias: nodegroupAlias },
        };
    }

    function section(...components: ComponentNode[]): ComponentNode {
        return { component: "app/ReportSection", config: { components } };
    }

    it("drops folios whose card is hidden and containers left empty", () => {
        expect(
            withoutHiddenCards(
                [
                    section(section(folio("statements"))),
                    section(
                        folio("statements"),
                        folio("names"),
                        folio("unknown"),
                    ),
                    section(),
                ],
                configs,
            ),
        ).toEqual([section(folio("names"), folio("unknown")), section()]);
    });
});
