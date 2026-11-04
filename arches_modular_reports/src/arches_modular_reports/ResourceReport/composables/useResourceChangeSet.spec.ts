import { effectScope } from "vue";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises } from "@vue/test-utils";

import { useResourceChangeSet } from "@/arches_modular_reports/ResourceReport/composables/useResourceChangeSet.ts";
import { nodegroupTiles } from "@/arches_modular_reports/ResourceReport/utils/tiles.ts";

import type {
    AliasedData,
    AliasedNodeData,
    AliasedTileData,
} from "@/arches_vue_components/types.ts";
import type {
    AliasedResourceData,
    ResourceChange,
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
let postResponse: () => Response = () => respondWith(serverResource);

function respondWith(body: unknown, status = 200): Response {
    return new Response(JSON.stringify(body), { status });
}

function conflictResponse(
    conflicts: unknown[],
    resource: AliasedResourceData,
): Response {
    return respondWith({ message: "Conflicts", conflicts, resource }, 409);
}

function postedChanges(): ResourceChange[] {
    const postRequest = vi
        .mocked(fetch)
        .mock.calls.filter(([, init]) => init?.method === "POST")
        .at(-1);
    return JSON.parse(String(postRequest?.[1]?.body)).changes;
}

function deferPost(): () => void {
    let finishPost: () => void = () => undefined;
    vi.mocked(fetch).mockImplementation((_url, init) => {
        if (init?.method !== "POST") {
            return Promise.resolve(respondWith(serverResource));
        }
        return new Promise((resolve) => {
            finishPost = () => resolve(respondWith(serverResource));
        });
    });
    return () => finishPost();
}

function serverWith(names: AliasedTileData[]): AliasedResourceData {
    return {
        resourceinstanceid: "resource",
        aliased_data: { names },
    };
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
        postResponse = () => respondWith(serverResource);
        vi.stubGlobal(
            "fetch",
            vi.fn((_url: string, init?: RequestInit) =>
                Promise.resolve(
                    init?.method === "POST"
                        ? postResponse()
                        : respondWith(serverResource),
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

    it("ignores another add while one is in flight", async () => {
        const changeSet = await createChangeSet();

        const [firstTileId, secondTileId] = await Promise.all([
            changeSet.addTile("names", null),
            changeSet.addTile("names", null),
        ]);

        expect(firstTileId).not.toBeNull();
        expect(secondTileId).toBeNull();
        expect(changeSet.pendingChanges.value).toHaveLength(1);
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

    it("sends files as multipart", async () => {
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
        const postRequest = vi
            .mocked(fetch)
            .mock.calls.find(([, init]) => init?.method === "POST");
        const body = postRequest?.[1]?.body;
        expect(body).toBeInstanceOf(FormData);
        const formData = body as FormData;
        expect(JSON.parse(String(formData.get("json"))).changes).toMatchObject([
            {
                type: "edit",
                tileId: "smalt",
                original: { name_content: "Smalt" },
            },
        ]);
        expect(formData.get("file-list_smalt-image-node")).toBeInstanceOf(File);
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
        const finishPost = deferPost();

        const saving = changeSet.save();
        await flushPromises();
        changeSet.editTile("names", "cobalt", {
            name_content: nodeData("Cobalt green"),
        });
        finishPost();

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
        const finishPost = deferPost();

        const saving = changeSet.save();
        await flushPromises();
        changeSet.editTile("names", newTileId, {
            name_content: nodeData("Ultramarine"),
        });
        serverResource = serverWith([
            ...nodegroupTiles(RESOURCE.aliased_data.names),
            makeTile(newTileId, 2, { name_content: nodeData("") }),
        ]);
        finishPost();
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

    it("saves without fetching the resource first", async () => {
        const changeSet = await createChangeSet();
        changeSet.editTile("names", "smalt", {
            name_content: nodeData("Smalt blue"),
        });
        serverResource = serverWith([
            makeTile("smalt", 0, { name_content: nodeData("Smalt blue") }),
        ]);

        expect(await changeSet.save()).toBe(true);

        const methods = vi
            .mocked(fetch)
            .mock.calls.map(([, init]) => init?.method ?? "GET");
        expect(methods).toEqual(["GET", "POST"]);
        expect(postedChanges()).toMatchObject([
            {
                type: "edit",
                tileId: "smalt",
                original: { name_content: "Smalt" },
            },
        ]);
        expect(changeSet.pendingChanges.value).toEqual([]);
        expect(
            nodegroupTiles(changeSet.workingResource.value?.aliased_data.names),
        ).toHaveLength(1);
    });

    it("keeps the first original across later edits to the same node", async () => {
        const changeSet = await createChangeSet();

        changeSet.editTile("names", "smalt", {
            name_content: nodeData("Smalt blue"),
        });
        changeSet.editTile("names", "smalt", {
            name_content: nodeData("Smalt navy"),
        });

        expect(changeSet.pendingChanges.value).toMatchObject([
            { original: { name_content: "Smalt" } },
        ]);
    });

    it("re-anchors originals of edits made during a save", async () => {
        const changeSet = await createChangeSet();
        changeSet.editTile("names", "smalt", {
            name_content: nodeData("Smalt blue"),
        });
        const finishPost = deferPost();

        const saving = changeSet.save();
        await flushPromises();
        changeSet.editTile("names", "smalt", {
            name_content: nodeData("Smalt navy"),
        });
        serverResource = serverWith([
            makeTile("smalt", 0, { name_content: nodeData("Smalt blue") }),
        ]);
        finishPost();
        await saving;

        expect(changeSet.pendingChanges.value).toMatchObject([
            { original: { name_content: "Smalt blue" } },
        ]);
    });

    describe("on a 409", () => {
        function modifiedConflict(changeId: string, tileId: string) {
            return {
                changeId,
                reason: "modified",
                nodegroupAlias: "names",
                tileId,
                nodes: {
                    name_content: {
                        current: "Renamed",
                        currentDisplay: "Renamed",
                        original: "Smalt",
                    },
                },
            };
        }

        it("keeps every pending change, shows current data, and marks the conflicts", async () => {
            const changeSet = await createChangeSet();
            changeSet.editTile("names", "smalt", {
                name_content: nodeData("Smalt blue"),
            });
            changeSet.deleteTile("names", "cobalt");
            const [edit] = changeSet.pendingChanges.value;
            postResponse = () =>
                conflictResponse(
                    [modifiedConflict(edit.id, "smalt")],
                    serverWith([
                        makeTile("smalt", 0, {
                            name_content: nodeData("Renamed"),
                        }),
                        ...nodegroupTiles(RESOURCE.aliased_data.names).slice(1),
                    ]),
                );

            expect(await changeSet.save()).toBe(false);

            expect(changeSet.pendingChanges.value).toHaveLength(2);
            expect(changeSet.conflicts.value).toMatchObject([
                { changeId: edit.id, reason: "modified" },
            ]);
            expect(changeSet.saveError.value).toBeNull();
            expect(
                nodegroupTiles(
                    changeSet.workingResource.value?.aliased_data.names,
                )[0].aliased_data.name_content,
            ).toMatchObject({ node_value: "Smalt blue" });
        });

        it("keeps mine for a modified conflict by adopting the server value as the original", async () => {
            const changeSet = await createChangeSet();
            changeSet.editTile("names", "smalt", {
                name_content: nodeData("Smalt blue"),
            });
            const [edit] = changeSet.pendingChanges.value;
            const currentResource = serverWith([
                makeTile("smalt", 0, { name_content: nodeData("Renamed") }),
            ]);
            postResponse = () =>
                conflictResponse(
                    [modifiedConflict(edit.id, "smalt")],
                    currentResource,
                );
            await changeSet.save();

            changeSet.keepMine(edit.id);

            expect(changeSet.conflicts.value).toEqual([]);
            expect(changeSet.conflictsResolved.value).toBe(true);
            serverResource = currentResource;
            postResponse = () => respondWith(currentResource);
            expect(await changeSet.save()).toBe(true);
            expect(postedChanges()).toMatchObject([
                { original: { name_content: "Renamed" } },
            ]);
        });

        it("uses theirs for a modified conflict by discarding the change", async () => {
            const changeSet = await createChangeSet();
            changeSet.editTile("names", "smalt", {
                name_content: nodeData("Smalt blue"),
            });
            const [edit] = changeSet.pendingChanges.value;
            postResponse = () =>
                conflictResponse(
                    [modifiedConflict(edit.id, "smalt")],
                    serverWith([
                        makeTile("smalt", 0, {
                            name_content: nodeData("Renamed"),
                        }),
                    ]),
                );
            await changeSet.save();

            changeSet.useTheirs(edit.id);

            expect(changeSet.pendingChanges.value).toEqual([]);
            expect(changeSet.conflicts.value).toEqual([]);
        });

        it("uses theirs only for the conflicting nodes of an edit", async () => {
            const changeSet = await createChangeSet();
            changeSet.editTile("names", "smalt", {
                name_content: nodeData("Smalt blue"),
                name_other: nodeData("Other"),
            });
            const [edit] = changeSet.pendingChanges.value;
            postResponse = () =>
                conflictResponse(
                    [modifiedConflict(edit.id, "smalt")],
                    serverWith([
                        makeTile("smalt", 0, {
                            name_content: nodeData("Renamed"),
                        }),
                    ]),
                );
            await changeSet.save();

            changeSet.useTheirs(edit.id);

            expect(changeSet.conflicts.value).toEqual([]);
            expect(changeSet.pendingChanges.value).toHaveLength(1);
            const [remaining] = changeSet.pendingChanges.value;
            if (remaining.type !== "edit") {
                throw new Error("Expected an edit.");
            }
            expect(Object.keys(remaining.aliasedData)).toEqual(["name_other"]);
            expect(Object.keys(remaining.original)).toEqual(["name_other"]);
        });

        it("restores a deleted tile as an add with the user's values", async () => {
            const changeSet = await createChangeSet();
            changeSet.editTile("names", "smalt", {
                name_content: nodeData("Smalt blue"),
            });
            const [edit] = changeSet.pendingChanges.value;
            postResponse = () =>
                conflictResponse(
                    [
                        {
                            changeId: edit.id,
                            reason: "deleted",
                            nodegroupAlias: "names",
                            tileId: "smalt",
                        },
                    ],
                    serverWith(
                        nodegroupTiles(RESOURCE.aliased_data.names).slice(1),
                    ),
                );
            await changeSet.save();
            expect(changeSet.conflicts.value[0].tileSnapshot?.tileid).toBe(
                "smalt",
            );

            changeSet.keepMine(edit.id);

            expect(changeSet.conflicts.value).toEqual([]);
            expect(changeSet.pendingChanges.value).toMatchObject([
                {
                    type: "add",
                    parentTileId: null,
                    tile: {
                        tileid: "smalt",
                        aliased_data: {
                            name_content: { node_value: "Smalt blue" },
                            name_notes: [],
                        },
                    },
                },
            ]);
            expect(
                nodegroupTiles(
                    changeSet.workingResource.value?.aliased_data.names,
                ).map((tile) => tile.tileid),
            ).toContain("smalt");
        });

        it("replaces the tile that took a single-tile slot", async () => {
            const changeSet = await createChangeSet();
            const addedTileId = await changeSet.addTile("description", null);
            if (addedTileId === null) {
                throw new Error("The tile was not added.");
            }
            changeSet.editTile("description", addedTileId, {
                name_content: nodeData("Mine"),
            });
            const [add] = changeSet.pendingChanges.value;
            postResponse = () =>
                conflictResponse(
                    [
                        {
                            changeId: add.id,
                            reason: "slot_taken",
                            nodegroupAlias: "description",
                            tileId: addedTileId,
                        },
                    ],
                    {
                        ...RESOURCE,
                        aliased_data: {
                            ...RESOURCE.aliased_data,
                            description: makeTile("theirs", 0, {
                                name_content: nodeData("Theirs"),
                            }),
                        },
                    },
                );
            await changeSet.save();

            changeSet.keepMine(add.id);

            expect(changeSet.conflicts.value).toEqual([]);
            expect(changeSet.pendingChanges.value).toMatchObject([
                {
                    type: "edit",
                    tileId: "theirs",
                    aliasedData: { name_content: { node_value: "Mine" } },
                    original: { name_content: "Theirs" },
                },
            ]);
        });

        it("offers only discard for a change whose parent was deleted", async () => {
            const changeSet = await createChangeSet();
            const noteTileId = await changeSet.addTile("name_notes", "cobalt");
            const [add] = changeSet.pendingChanges.value;
            postResponse = () =>
                conflictResponse(
                    [
                        {
                            changeId: add.id,
                            reason: "parent_deleted",
                            nodegroupAlias: "name_notes",
                            tileId: noteTileId,
                        },
                    ],
                    serverWith(
                        nodegroupTiles(RESOURCE.aliased_data.names).slice(0, 1),
                    ),
                );
            await changeSet.save();

            changeSet.keepMine(add.id);
            expect(changeSet.conflicts.value).toHaveLength(1);
            expect(changeSet.pendingChanges.value).toHaveLength(1);

            changeSet.discardChange(add.id);
            expect(changeSet.pendingChanges.value).toEqual([]);
            expect(changeSet.conflicts.value).toEqual([]);
        });

        it("resolves every conflict at once", async () => {
            const changeSet = await createChangeSet();
            changeSet.editTile("names", "smalt", {
                name_content: nodeData("Smalt blue"),
            });
            changeSet.editTile("names", "cobalt", {
                name_content: nodeData("Cobalt green"),
            });
            const [smaltEdit, cobaltEdit] = changeSet.pendingChanges.value;
            postResponse = () =>
                conflictResponse(
                    [
                        modifiedConflict(smaltEdit.id, "smalt"),
                        modifiedConflict(cobaltEdit.id, "cobalt"),
                    ],
                    serverWith([
                        makeTile("smalt", 0, {
                            name_content: nodeData("Renamed"),
                        }),
                        makeTile("cobalt", 1, {
                            name_content: nodeData("Renamed"),
                        }),
                    ]),
                );
            await changeSet.save();
            expect(changeSet.conflicts.value).toHaveLength(2);

            changeSet.keepAllMine();
            expect(changeSet.conflicts.value).toEqual([]);
            expect(changeSet.pendingChanges.value).toMatchObject([
                { original: { name_content: "Renamed" } },
                { original: { name_content: "Renamed" } },
            ]);

            await changeSet.save();
            expect(changeSet.conflicts.value).toHaveLength(2);

            changeSet.discardAllConflicting();
            expect(changeSet.pendingChanges.value).toEqual([]);
            expect(changeSet.conflicts.value).toEqual([]);
        });

        it("reports a non-conflict failure as a save error", async () => {
            const changeSet = await createChangeSet();
            changeSet.editTile("names", "smalt", {
                name_content: nodeData("Smalt blue"),
            });
            postResponse = () => respondWith({ message: "Invalid" }, 400);

            expect(await changeSet.save()).toBe(false);
            expect(changeSet.conflicts.value).toEqual([]);
            expect(changeSet.pendingChanges.value).toHaveLength(1);
        });
    });
});
