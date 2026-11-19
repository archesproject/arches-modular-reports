import { describe, expect, it } from "vitest";

import {
    hasOtherLanguages,
    localizedTexts,
    nodeHasData,
    nodeSearchTexts,
    nodeText,
} from "@/arches_modular_reports/ResourceReport/utils/localized-text.ts";
import {
    tileHasData,
    tileSummary,
} from "@/arches_modular_reports/ResourceReport/utils/tiles.ts";

import type {
    AliasedNodeData,
    AliasedTileData,
    NodegroupWidgetConfig,
} from "@/arches_vue_components/types.ts";

const GERMAN_ONLY: AliasedNodeData = {
    display_value: "",
    node_value: {
        en: { value: "", direction: "ltr" },
        de: { value: "<p>Mythische&nbsp;Figur</p>", direction: "ltr" },
    },
    details: [],
};

const BOTH: AliasedNodeData = {
    display_value: "Cobalt blue",
    node_value: {
        de: { value: "Kobaltblau", direction: "ltr" },
        en: { value: "Cobalt blue", direction: "ltr" },
    },
    details: [],
};

const NUMBER: AliasedNodeData = {
    display_value: "42",
    node_value: 42,
    details: [],
};

function tileWith(nodeData: AliasedNodeData): AliasedTileData {
    return {
        aliased_data: { name_content: nodeData },
        nodegroup: "names",
        parenttile: null,
        provisionaledits: null,
        resourceinstance: "resource-id",
        sortorder: 0,
        tileid: "tile-id",
    } as AliasedTileData;
}

describe("localizedTexts", () => {
    it("puts the reader's language first and drops blank languages", () => {
        expect(
            localizedTexts(BOTH, "en").map((text) => text.languageCode),
        ).toEqual(["en", "de"]);
        expect(
            localizedTexts(GERMAN_ONLY, "en").map((text) => text.languageCode),
        ).toEqual(["de"]);
    });

    it("has nothing to say about values that aren't multilingual text", () => {
        expect(localizedTexts(NUMBER, "en")).toEqual([]);
        expect(localizedTexts(null, "en")).toEqual([]);
    });

    it("tells when a value has text outside the reader's language", () => {
        expect(hasOtherLanguages(localizedTexts(BOTH, "en"), "en")).toBe(true);
        expect(
            hasOtherLanguages(
                localizedTexts(
                    {
                        ...BOTH,
                        node_value: {
                            en: { value: "Cobalt blue", direction: "ltr" },
                        },
                    },
                    "en",
                ),
                "en",
            ),
        ).toBe(false);
    });
});

describe("nodeText", () => {
    it("prefers the display value", () => {
        expect(nodeText(BOTH)).toBe("Cobalt blue");
        expect(nodeText(NUMBER)).toBe("42");
    });

    it("falls back to another language's plain text", () => {
        expect(nodeText(GERMAN_ONLY)).toBe("Mythische Figur");
    });

    it("counts only real text as data", () => {
        expect(nodeHasData(GERMAN_ONLY)).toBe(true);
        expect(
            nodeHasData({
                display_value: "  ",
                node_value: { en: { value: " ", direction: "ltr" } },
                details: [],
            }),
        ).toBe(false);
        expect(nodeHasData(null)).toBe(false);
    });

    it("searches every language", () => {
        expect(nodeSearchTexts(BOTH)).toEqual(["Kobaltblau", "Cobalt blue"]);
        expect(nodeSearchTexts(NUMBER)).toEqual(["42"]);
    });
});

describe("tiles holding text in another language", () => {
    it("have data, and a summary", () => {
        const tile = tileWith(GERMAN_ONLY);

        expect(tileHasData(tile)).toBe(true);
        expect(
            tileSummary(tile, {
                card_x_node_x_widgets: [
                    { visible: true, node: { alias: "name_content" } },
                ],
            } as NodegroupWidgetConfig),
        ).toBe("Mythische Figur");
    });
});
