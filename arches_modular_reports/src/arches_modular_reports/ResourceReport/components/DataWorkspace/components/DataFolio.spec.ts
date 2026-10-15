import { effectScope } from "vue";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import OpenVue from "openvue/config";

import DataFolio from "@/arches_modular_reports/ResourceReport/components/DataWorkspace/components/DataFolio.vue";
import { useResourceChangeSet } from "@/arches_modular_reports/ResourceReport/composables/useResourceChangeSet.ts";
import { nodegroupTiles } from "@/arches_modular_reports/ResourceReport/utils/tiles.ts";

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

vi.mock("@/arches_vue_components/generics/GenericCard/api.ts", () => ({
    fetchTileData: () =>
        Promise.resolve({
            aliased_data: {},
            nodegroup: "nodegroup",
            parenttile: null,
            provisionaledits: null,
            resourceinstance: "",
            sortorder: 0,
            tileid: null,
        }),
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
    description: makeNodegroupWidgetConfig(
        null,
        "1",
        makeWidget("description_content", "Description"),
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
        description: makeTile("description", 0, {
            description_content: nodeData("Blue"),
        }),
    },
};

async function mountEditor(nodegroupAlias: string, filterText = "") {
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
            filterText,
            selectedTileId: null,
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

function tileRow(
    wrapper: Awaited<ReturnType<typeof mountEditor>>["wrapper"],
    summary: string,
) {
    const row = wrapper
        .findAll(".data-folio-tile")
        .find((tile) => tile.find(".data-folio-summary").text() === summary);
    if (row === undefined) {
        throw new Error(`No tile row for ${summary}`);
    }
    return row;
}

function rowButton(row: ReturnType<typeof tileRow>, label: string) {
    const button = row
        .find(".data-folio-tile-row")
        .findAll("button")
        .find(
            (candidate) =>
                candidate.text() === label ||
                candidate.attributes("aria-label") === label,
        );
    if (button === undefined) {
        throw new Error(`No ${label} button`);
    }
    return button;
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

    it("offers Add only where the nodegroup can take another tile", async () => {
        expect(
            (await mountEditor("names")).wrapper
                .find(".data-folio-add")
                .exists(),
        ).toBe(true);
        expect(
            (await mountEditor("description")).wrapper
                .find(".data-folio-add")
                .exists(),
        ).toBe(false);
    });

    it("adds a tile and asks for it to be edited", async () => {
        const { changeSet, wrapper } = await mountEditor("names");

        await wrapper.find(".data-folio-add").trigger("click");
        await flushPromises();

        const addedChange = changeSet.pendingChanges.value[0];
        if (addedChange.type !== "add") {
            throw new Error("The first pending change is not an add.");
        }
        expect(wrapper.emitted("edit-tile")).toEqual([
            [{ nodegroupAlias: "names", tileId: addedChange.tile.tileid }],
        ]);
    });

    it("locks a deleted tile's descendants until the delete is undone", async () => {
        const { changeSet, wrapper } = await mountEditor("names");

        await rowButton(
            tileRow(wrapper, "Cobalt"),
            "Show details for Cobalt",
        ).trigger("click");
        await rowButton(tileRow(wrapper, "Cobalt"), "Delete").trigger("click");

        const noteRow = tileRow(wrapper, "Glass");
        expect(noteRow.classes()).toContain("data-folio-tile-deleted");
        expect(noteRow.find(".data-folio-tile-actions").exists()).toBe(false);

        await rowButton(tileRow(wrapper, "Cobalt"), "Undo delete").trigger(
            "click",
        );
        expect(changeSet.pendingChanges.value).toEqual([]);
    });

    it("reorders tiles with the move buttons and clears the reorder when dragged back", async () => {
        const { changeSet, wrapper } = await mountEditor("names");

        await rowButton(tileRow(wrapper, "Cobalt"), "Move Cobalt up").trigger(
            "click",
        );
        expect(changeSet.pendingChanges.value).toMatchObject([
            { type: "reorder", tileIds: ["cobalt", "smalt"] },
        ]);

        await wrapper.setProps({ tiles: workingTiles(changeSet, "names") });
        await tileRow(wrapper, "Smalt")
            .find(".data-folio-tile-row")
            .trigger("dragstart");
        await tileRow(wrapper, "Cobalt").trigger("drop");
        expect(changeSet.pendingChanges.value).toEqual([]);
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

    it("expands to and highlights tiles matching the filter", async () => {
        const { wrapper } = await mountEditor("names", "glass");

        expect(tileRow(wrapper, "Glass").classes()).toContain(
            "data-folio-tile-match",
        );
        expect(
            tileRow(wrapper, "Smalt").find(".data-folio-tile-body").exists(),
        ).toBe(false);
    });
});
