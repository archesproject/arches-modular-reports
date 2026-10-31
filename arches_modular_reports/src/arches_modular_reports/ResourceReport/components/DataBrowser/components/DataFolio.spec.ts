import { effectScope } from "vue";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import OpenVue from "openvue/config";

import DataFolio from "@/arches_modular_reports/ResourceReport/components/DataBrowser/components/DataFolio.vue";
import { useResourceChangeSet } from "@/arches_modular_reports/ResourceReport/composables/useResourceChangeSet.ts";
import { nodegroupTiles } from "@/arches_modular_reports/ResourceReport/utils/tiles.ts";

import type { DOMWrapper, VueWrapper } from "@vue/test-utils";
import type {
    AliasedData,
    AliasedNodeData,
    AliasedTileData,
    CardXNodeXWidgetData,
    NodegroupWidgetConfig,
} from "@/arches_vue_components/types.ts";
import type {
    AliasedResourceData,
    ResourceChangeSet,
} from "@/arches_modular_reports/ResourceReport/types.ts";

vi.mock("@/arches_vue_components/application/generate-arches-url.ts", () => ({
    generateArchesURL: (urlName: string) => urlName,
}));

function makeWidget(nodeAlias: string, label: string): CardXNodeXWidgetData {
    return {
        card: {
            name: label,
            sortorder: 0,
            cardid: `${nodeAlias}-card`,
            nodegroup_id: `${nodeAlias}-nodegroup`,
            nodes: [],
            visible: true,
        },
        config: {},
        id: `${nodeAlias}-widget`,
        label,
        node: {
            alias: nodeAlias,
            isrequired: false,
            nodeid: `${nodeAlias}-node`,
            datatype: "string",
            config: {},
        },
        sortorder: 0,
        visible: true,
        widget: { widgetid: "text-widget", component: "TextWidget" },
    };
}

function makeNodegroupWidgetConfig(
    parentNodegroupAlias: string | null,
    cardinality: string,
    widget: CardXNodeXWidgetData,
): NodegroupWidgetConfig {
    return {
        parent_nodegroup_alias: parentNodegroupAlias,
        cardinality,
        is_writable: true,
        card: widget.card,
        card_x_node_x_widgets: [widget],
    };
}

function nodeData(value: string): AliasedNodeData {
    return { display_value: value, node_value: value, details: [] };
}

function makeTile(
    tileid: string,
    sortorder: number,
    aliasedData: AliasedData,
): AliasedTileData {
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

const NODEGROUP_WIDGET_CONFIGS = {
    names: makeNodegroupWidgetConfig(
        null,
        "n",
        makeWidget("name_content", "Name"),
    ),
    name_notes: makeNodegroupWidgetConfig(
        "names",
        "n",
        makeWidget("note_content", "Note"),
    ),
    origin: makeNodegroupWidgetConfig(
        null,
        "1",
        makeWidget("origin_place", "Place"),
    ),
};

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
                name_notes: [
                    makeTile("note", 0, { note_content: nodeData("Glass") }),
                ],
            }),
        ],
        origin: makeTile("origin", 0, { origin_place: nodeData("Saxony") }),
    },
};

async function mountEditor(
    nodegroupAlias: string,
    query = "",
): Promise<{ changeSet: ResourceChangeSet; wrapper: VueWrapper }> {
    const changeSet = effectScope().run(() =>
        useResourceChangeSet("pigment", "resource"),
    );
    if (changeSet === undefined) {
        throw new Error("The effect scope is inactive.");
    }
    await flushPromises();
    const wrapper = mount(DataFolio, {
        props: {
            nodegroupAlias,
            nodegroupWidgetConfigs: NODEGROUP_WIDGET_CONFIGS,
            tiles: workingTiles(changeSet, nodegroupAlias),
            parentTileId: null,
            changeSet,
            query,
            matchedByAncestor: false,
            selectedTileId: null,
            isEditable: true,
        },
        global: { plugins: [[OpenVue, { theme: "none" }]] },
    });
    return { changeSet, wrapper };
}

function workingTiles(
    changeSet: ResourceChangeSet,
    nodegroupAlias: string,
): AliasedTileData[] {
    return nodegroupTiles(
        changeSet.workingResource.value?.aliased_data[nodegroupAlias],
    );
}

function tileRow(wrapper: VueWrapper, summary: string): DOMWrapper<Element> {
    const row = wrapper
        .findAll(".data-folio-tile")
        .find((tile) => tile.find(".data-folio-summary").text() === summary);
    if (row === undefined) {
        throw new Error(`No tile row for ${summary}`);
    }
    return row;
}

function topLevelSummaries(wrapper: VueWrapper): string[] {
    return [...wrapper.find(".data-folio-tiles").element.children].map(
        (tile) =>
            tile.querySelector(".data-folio-summary")?.textContent?.trim() ??
            "",
    );
}

describe("DataFolio", () => {
    beforeEach(() => {
        vi.stubGlobal(
            "fetch",
            vi.fn(() =>
                Promise.resolve(
                    new Response(JSON.stringify(RESOURCE), { status: 200 }),
                ),
            ),
        );
    });

    it("starts collapsed and expands to show its entries", async () => {
        const { wrapper } = await mountEditor("names");
        expect(wrapper.find(".data-folio-tiles").exists()).toBe(false);

        await wrapper
            .find(".data-folio-header [aria-expanded]")
            .trigger("click");

        expect(topLevelSummaries(wrapper)).toEqual(["Smalt", "Cobalt"]);
    });

    it("shows a nested card's fields open even without entries", async () => {
        const { wrapper } = await mountEditor("name_notes");
        expect(
            wrapper.find(".data-folio-header [aria-expanded]").exists(),
        ).toBe(false);

        const field = wrapper.find(".data-folio-placeholder .data-folio-field");
        expect(field.find("dt").text()).toBe("Note");
        expect(field.find("dd").text()).toBe("—");
    });

    it("lists a single entry's fields with its actions in the header", async () => {
        const { wrapper } = await mountEditor("origin");
        await wrapper
            .find(".data-folio-header [aria-expanded]")
            .trigger("click");

        expect(wrapper.find(".data-folio-tile-row").exists()).toBe(false);
        expect(wrapper.find(".data-folio-field dd").text()).toBe("Saxony");
        expect(
            wrapper
                .find(".data-folio-header .data-folio-tile-actions")
                .exists(),
        ).toBe(true);
    });

    it("collapses a tile that the filter expanded", async () => {
        const { wrapper } = await mountEditor("names", "glass");
        expect(
            tileRow(wrapper, "Cobalt").find(".data-folio-tile-body").exists(),
        ).toBe(true);

        await tileRow(wrapper, "Cobalt")
            .find(".data-folio-tile-row [aria-expanded]")
            .trigger("click");

        expect(
            tileRow(wrapper, "Cobalt").find(".data-folio-tile-body").exists(),
        ).toBe(false);
    });

    it("hides entries without a match unless a field label matches", async () => {
        const { wrapper: valueMatch } = await mountEditor("names", "glass");
        expect(topLevelSummaries(valueMatch)).toEqual(["Cobalt"]);
        expect(valueMatch.find("mark").text()).toBe("Glass");

        const { wrapper: labelMatch } = await mountEditor("names", "name");
        expect(topLevelSummaries(labelMatch)).toEqual(["Smalt", "Cobalt"]);
    });
});
