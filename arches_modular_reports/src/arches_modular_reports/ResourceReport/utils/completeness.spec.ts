import { describe, expect, it } from "vitest";

import {
    completenessCards,
    groupCardsByReportTab,
} from "@/arches_modular_reports/ResourceReport/utils/completeness.ts";

import type {
    AliasedTileData,
    NodegroupWidgetConfig,
} from "@/arches_vue_components/types.ts";
import type { NodeTextContext } from "@/arches_modular_reports/ResourceReport/types.ts";
import type { CompletenessCard } from "@/arches_modular_reports/ResourceReport/utils/completeness.ts";

const NODE_TEXT_CONTEXT: NodeTextContext = {
    richTextNodeAliases: new Set(),
    activeLanguage: "",
    defaultLanguage: "",
};

function nodegroupConfig({
    name,
    sortorder,
    parent = null,
    cardinality = "n",
    isRequired = false,
    isVisible = true,
}: {
    name: string;
    sortorder: number;
    parent?: string | null;
    cardinality?: "1" | "n";
    isRequired?: boolean;
    isVisible?: boolean;
}): NodegroupWidgetConfig {
    return {
        parent_nodegroup_alias: parent,
        cardinality,
        is_writable: true,
        card: {
            name,
            sortorder,
            cardid: `${name}-card`,
            nodegroup_id: `${name}-nodegroup`,
            nodes: [],
            visible: isVisible,
        },
        card_x_node_x_widgets: [
            {
                card: {
                    name,
                    sortorder,
                    cardid: `${name}-card`,
                    nodegroup_id: `${name}-nodegroup`,
                    nodes: [],
                    visible: isVisible,
                },
                config: {},
                id: `${name}-widget`,
                label: name,
                node: {
                    alias: `${name}_content`,
                    isrequired: isRequired,
                    nodeid: `${name}-node`,
                    datatype: "string",
                    config: {},
                },
                sortorder: 0,
                visible: true,
                widget: { widgetid: "text-widget", component: "TextWidget" },
            },
        ],
    };
}

function tile(tileId: string, value: string): AliasedTileData {
    return {
        aliased_data: {
            content: { display_value: value, node_value: value, details: [] },
        },
        nodegroup: "nodegroup",
        parenttile: null,
        provisionaledits: null,
        resourceinstance: "resource-id",
        sortorder: 0,
        tileid: tileId,
    };
}

const NODEGROUP_WIDGET_CONFIGS: Record<string, NodegroupWidgetConfig> = {
    names: nodegroupConfig({ name: "Name", sortorder: 1 }),
    owner: nodegroupConfig({
        name: "Current Owner",
        sortorder: 2,
        cardinality: "1",
        isRequired: true,
    }),
    colors: nodegroupConfig({ name: "Color", sortorder: 3 }),
    color_names: nodegroupConfig({
        name: "Color Name",
        sortorder: 0,
        parent: "colors",
    }),
    hidden: nodegroupConfig({
        name: "Hidden",
        sortorder: 4,
        isVisible: false,
    }),
};

function card(nodegroupAlias: string): CompletenessCard {
    return {
        nodegroupAlias,
        name: nodegroupAlias,
        hasData: false,
        isRequired: false,
    };
}

describe("completenessCards", () => {
    it("has data once an entry holds a value and is not being deleted", () => {
        const cards = completenessCards(
            NODEGROUP_WIDGET_CONFIGS,
            {
                names: [tile("blank", ""), tile("doomed", "Cobalt")],
                owner: tile("owner", "Getty"),
            },
            (tileId) => tileId === "doomed",
            NODE_TEXT_CONTEXT,
        );

        expect(
            cards.map((completenessCard) => completenessCard.hasData),
        ).toEqual([false, true, false]);
    });
});

describe("groupCardsByReportTab", () => {
    it("groups cards by the tab showing them, then lists the rest", () => {
        const groups = groupCardsByReportTab(
            [card("names"), card("owner"), card("colors")],
            [
                { label: "Overview", nodegroupAliases: ["owner", "names"] },
                { label: "Physical", nodegroupAliases: ["color_names"] },
            ],
            NODEGROUP_WIDGET_CONFIGS,
        );

        expect(
            groups.map((group) => ({
                tabLabel: group.tabLabel,
                aliases: group.cards.map(
                    (groupCard) => groupCard.nodegroupAlias,
                ),
            })),
        ).toEqual([
            { tabLabel: "Overview", aliases: ["owner", "names"] },
            { tabLabel: "Physical", aliases: ["colors"] },
        ]);
    });
});
