import { describe, expect, it } from "vitest";

import {
    localizedTexts,
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
import type { NodeTextContext } from "@/arches_modular_reports/ResourceReport/types.ts";

const NODE_TEXT_CONTEXT: NodeTextContext = {
    richTextNodeAliases: new Set(["name_content"]),
    activeLanguage: "en",
    defaultLanguage: "en",
};

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
            localizedTexts("name_content", BOTH, NODE_TEXT_CONTEXT).map(
                (text) => text.languageCode,
            ),
        ).toEqual(["en", "de"]);
        expect(
            localizedTexts("name_content", GERMAN_ONLY, NODE_TEXT_CONTEXT).map(
                (text) => text.languageCode,
            ),
        ).toEqual(["de"]);
    });
});

describe("nodeText", () => {
    it("falls back to another language's plain text", () => {
        expect(nodeText("name_content", GERMAN_ONLY, NODE_TEXT_CONTEXT)).toBe(
            "Mythische Figur",
        );
    });

    it("prefers the default language and leaves plain text alone", () => {
        const germanAndFrench: AliasedNodeData = {
            display_value: "",
            node_value: {
                de: { value: "Kobaltblau", direction: "ltr" },
                fr: { value: "Bleu de cobalt", direction: "ltr" },
            },
            details: [],
        };
        const plainNote: AliasedNodeData = {
            display_value: "pH<neutral after firing",
            node_value: {
                en: { value: "pH<neutral after firing", direction: "ltr" },
            },
            details: [],
        };

        expect(
            nodeText("note_content", germanAndFrench, {
                ...NODE_TEXT_CONTEXT,
                defaultLanguage: "fr",
            }),
        ).toBe("Bleu de cobalt");
        expect(nodeText("note_content", plainNote, NODE_TEXT_CONTEXT)).toBe(
            "pH<neutral after firing",
        );
    });
});

describe("tiles holding text in another language", () => {
    it("have data, and a summary", () => {
        const tile = tileWith(GERMAN_ONLY);

        expect(tileHasData(tile, NODE_TEXT_CONTEXT)).toBe(true);
        expect(
            tileSummary(
                tile,
                {
                    card_x_node_x_widgets: [
                        { visible: true, node: { alias: "name_content" } },
                    ],
                } as NodegroupWidgetConfig,
                NODE_TEXT_CONTEXT,
            ),
        ).toBe("Mythische Figur");
    });
});
