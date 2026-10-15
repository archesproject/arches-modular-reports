import { effectScope } from "vue";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises } from "@vue/test-utils";

import { fetchTileData } from "@/arches_vue_components/generics/GenericCard/api.ts";
import { useResourceChangeSet } from "@/arches_modular_reports/ResourceReport/composables/useResourceChangeSet.ts";
import { nodegroupTiles } from "@/arches_modular_reports/ResourceReport/utils/tiles.ts";

import type {
    AliasedData,
    AliasedNodeData,
    AliasedTileData,
} from "@/arches_vue_components/types.ts";
import type {
    AliasedResourceData,
    ResourceChangeSet,
} from "@/arches_modular_reports/ResourceReport/types.ts";

vi.mock("@/arches_vue_components/application/generate-arches-url.ts", () => ({
    generateArchesURL: (urlName: string) => urlName,
}));

vi.mock("@/arches_vue_components/generics/GenericCard/api.ts", () => ({
    fetchTileData: vi.fn(() =>
        Promise.resolve({
            aliased_data: {
                name_content: {
                    display_value: "",
                    node_value: null,
                    details: [],
                },
                name_notes: [
                    {
                        aliased_data: {},
                        nodegroup: "nodegroup",
                        parenttile: null,
                        provisionaledits: null,
                        resourceinstance: "",
                        sortorder: 0,
                        tileid: null,
                    },
                ],
            },
            nodegroup: "nodegroup",
            parenttile: null,
            provisionaledits: null,
            resourceinstance: "",
            sortorder: 0,
            tileid: null,
        }),
    ),
}));

function nodeData(value: unknown): AliasedNodeData {
    return { display_value: String(value), node_value: value, details: [] };
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
    },
};

let serverResource: AliasedResourceData = RESOURCE;

function respondWith(body: unknown): Response {
    return new Response(JSON.stringify(body), { status: 200 });
}

function deferPut(): () => void {
    let finishPut: () => void = () => undefined;
    vi.mocked(fetch).mockImplementation((_url, init) => {
        if (init?.method !== "PUT") {
            return Promise.resolve(respondWith(serverResource));
        }
        return new Promise((resolve) => {
            finishPut = () =>
                resolve(respondWith(JSON.parse(String(init.body))));
        });
    });
    return () => finishPut();
}

async function createChangeSet(): Promise<ResourceChangeSet> {
    const changeSet = effectScope().run(() =>
        useResourceChangeSet("pigment", "resource"),
    );
    if (changeSet === undefined) {
        throw new Error("The effect scope is inactive.");
    }
    await flushPromises();
    return changeSet;
}

describe("useResourceChangeSet", () => {
    beforeEach(() => {
        serverResource = RESOURCE;
        vi.stubGlobal(
            "fetch",
            vi.fn((_url: string, init?: RequestInit) =>
                Promise.resolve(
                    respondWith(
                        init?.method === "PUT" ? RESOURCE : serverResource,
                    ),
                ),
            ),
        );
    });

    it("adds tiles without the blank child tiles they arrive with", async () => {
        const changeSet = await createChangeSet();

        await changeSet.addTile("names", null);
        await changeSet.addTile("names", null);

        const nameTiles = nodegroupTiles(
            changeSet.workingResource.value?.aliased_data.names,
        );
        expect(nameTiles).toHaveLength(4);
        expect(nameTiles[2].aliased_data.name_notes).toEqual([]);
    });

    it("reports a blank tile that cannot be fetched", async () => {
        const changeSet = await createChangeSet();
        vi.mocked(fetchTileData).mockRejectedValueOnce(new Error("Offline"));

        expect(await changeSet.addTile("names", null)).toBeNull();
        expect(changeSet.addError.value?.message).toBe("Offline");
        expect(changeSet.pendingChanges.value).toEqual([]);
    });

    it("discards everything added under a discarded add", async () => {
        const changeSet = await createChangeSet();

        const nameTileId = await changeSet.addTile("names", null);
        const noteTileId = await changeSet.addTile("name_notes", nameTileId);
        if (noteTileId === null) {
            throw new Error("The note tile was not added.");
        }
        changeSet.editTile("name_notes", noteTileId, {
            note_content: nodeData("Glaze"),
        });
        changeSet.discardChange(changeSet.pendingChanges.value[0].id);

        expect(changeSet.pendingChanges.value).toEqual([]);
    });

    it("marks a deleted tile's descendants until the delete is undone", async () => {
        const changeSet = await createChangeSet();

        changeSet.deleteTile("names", "cobalt");
        expect(changeSet.changeTypeForTile("cobalt")).toBe("delete");
        expect(changeSet.isPendingDelete("note")).toBe(true);

        changeSet.undoDelete("cobalt");
        expect(changeSet.isPendingDelete("note")).toBe(false);
    });

    it("saves onto a fresh copy and sends files as multipart", async () => {
        const changeSet = await createChangeSet();

        changeSet.editTile("names", "smalt", {
            name_content: nodeData([
                {
                    file: new File(["pigment"], "smalt.jpg"),
                    node_id: "image-node",
                },
            ]),
        });

        expect(await changeSet.save()).toBe(true);
        const putRequest = vi
            .mocked(fetch)
            .mock.calls.find(([, init]) => init?.method === "PUT");
        expect(putRequest?.[1]?.body).toBeInstanceOf(FormData);
        expect(changeSet.pendingChanges.value).toEqual([]);
    });

    it("drops an edit once its values match the server again", async () => {
        const changeSet = await createChangeSet();

        changeSet.editTile("names", "smalt", {
            name_content: nodeData("Smalt blue"),
        });
        changeSet.editTile("names", "smalt", {
            name_content: nodeData("Smalt"),
        });

        expect(changeSet.pendingChanges.value).toEqual([]);
    });

    it("drops a reorder back to the current order, even with a pending add", async () => {
        const changeSet = await createChangeSet();
        const newTileId = await changeSet.addTile("names", null);
        if (newTileId === null) {
            throw new Error("The tile was not added.");
        }

        changeSet.reorderTiles("names", null, [newTileId, "smalt", "cobalt"]);
        changeSet.reorderTiles("names", null, ["smalt", "cobalt", newTileId]);

        expect(
            changeSet.pendingChanges.value.map((change) => change.type),
        ).toEqual(["add"]);
    });

    it("keeps edits made while a save is in flight", async () => {
        const changeSet = await createChangeSet();
        changeSet.editTile("names", "smalt", {
            name_content: nodeData("Smalt blue"),
        });
        const finishPut = deferPut();

        const saving = changeSet.save();
        await flushPromises();
        changeSet.editTile("names", "cobalt", {
            name_content: nodeData("Cobalt green"),
        });
        finishPut();

        expect(await saving).toBe(true);
        expect(changeSet.pendingChanges.value).toMatchObject([
            { type: "edit", tileId: "cobalt" },
        ]);
    });

    it("turns an add edited during its save into an edit", async () => {
        const changeSet = await createChangeSet();
        const newTileId = await changeSet.addTile("names", null);
        if (newTileId === null) {
            throw new Error("The tile was not added.");
        }
        const finishPut = deferPut();

        const saving = changeSet.save();
        await flushPromises();
        changeSet.editTile("names", newTileId, {
            name_content: nodeData("Ultramarine"),
        });
        finishPut();
        await saving;

        expect(changeSet.pendingChanges.value).toMatchObject([
            {
                type: "edit",
                tileId: newTileId,
                aliasedData: { name_content: nodeData("Ultramarine") },
            },
        ]);
        expect(
            nodegroupTiles(
                changeSet.workingResource.value?.aliased_data.names,
            ).filter((tile) => tile.tileid === newTileId),
        ).toHaveLength(1);
    });

    it("refuses to save changes whose tiles have vanished", async () => {
        const changeSet = await createChangeSet();
        changeSet.editTile("names", "smalt", {
            name_content: nodeData("Smalt blue"),
        });
        serverResource = {
            resourceinstanceid: "resource",
            aliased_data: { names: [] },
        };

        expect(await changeSet.save()).toBe(false);
        expect(changeSet.conflictingChangeIds.value).toEqual([
            changeSet.pendingChanges.value[0].id,
        ]);
        expect(
            vi
                .mocked(fetch)
                .mock.calls.some(([, init]) => init?.method === "PUT"),
        ).toBe(false);
    });
});
