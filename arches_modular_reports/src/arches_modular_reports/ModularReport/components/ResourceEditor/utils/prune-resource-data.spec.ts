import { describe, expect, it } from "vitest";

import { pruneResourceData } from "@/arches_modular_reports/ModularReport/components/ResourceEditor/utils/prune-resource-data.ts";

import type { ResourceData } from "@/arches_modular_reports/ModularReport/types.ts";
import type { WidgetDirtyStates } from "@/arches_modular_reports/ModularReport/components/ResourceEditor/types.ts";
import type { AliasedTileData } from "@/arches_vue_components/types.ts";

const PERSISTED_TILE_ID = "11111111-1111-1111-1111-111111111111";
const CLIENT_GENERATED_TILE_ID = "22222222-2222-2222-2222-222222222222";

function makeTile(tileId: string | null): AliasedTileData {
    return {
        tileid: tileId,
        nodegroup: "33333333-3333-3333-3333-333333333333",
        parenttile: null,
        provisionaledits: null,
        resourceinstance: "44444444-4444-4444-4444-444444444444",
        sortorder: 0,
        aliased_data: {
            name_content: {
                node_value: null,
                display_value: "",
                details: [],
            },
        },
    } as unknown as AliasedTileData;
}

function makeResourceData(
    aliasedData: ResourceData["aliased_data"],
): ResourceData {
    return {
        resourceinstanceid: "55555555-5555-5555-5555-555555555555",
        aliased_data: aliasedData,
    } as ResourceData;
}

function makeDirtyStates(isNameContentDirty: boolean): WidgetDirtyStates {
    return {
        aliased_data: { name_content: isNameContentDirty },
    } as unknown as WidgetDirtyStates;
}

describe("pruneResourceData", () => {
    it("drops an untouched placeholder that was assigned a client-generated id", () => {
        const resourceData = makeResourceData({
            name: makeTile(CLIENT_GENERATED_TILE_ID),
        });
        const widgetDirtyStates = {
            aliased_data: { name: makeDirtyStates(false) },
        } as unknown as WidgetDirtyStates;

        const pruned = pruneResourceData(
            resourceData,
            widgetDirtyStates,
            new Set([CLIENT_GENERATED_TILE_ID]),
        );

        expect(Object.keys(pruned.aliased_data)).toEqual([]);
    });

    it("keeps an edited placeholder, preserving its client-generated id", () => {
        const resourceData = makeResourceData({
            name: makeTile(CLIENT_GENERATED_TILE_ID),
        });
        const widgetDirtyStates = {
            aliased_data: { name: makeDirtyStates(true) },
        } as unknown as WidgetDirtyStates;

        const pruned = pruneResourceData(
            resourceData,
            widgetDirtyStates,
            new Set([CLIENT_GENERATED_TILE_ID]),
        );

        expect(pruned.aliased_data.name).toMatchObject({
            tileid: CLIENT_GENERATED_TILE_ID,
        });
    });

    it("keeps an untouched persisted tile", () => {
        const resourceData = makeResourceData({
            name: makeTile(PERSISTED_TILE_ID),
        });
        const widgetDirtyStates = {
            aliased_data: { name: makeDirtyStates(false) },
        } as unknown as WidgetDirtyStates;

        const pruned = pruneResourceData(
            resourceData,
            widgetDirtyStates,
            new Set([CLIENT_GENERATED_TILE_ID]),
        );

        expect(pruned.aliased_data.name).toMatchObject({
            tileid: PERSISTED_TILE_ID,
        });
    });

    it("drops an untouched tile that has no id at all", () => {
        const resourceData = makeResourceData({ name: makeTile(null) });
        const widgetDirtyStates = {
            aliased_data: { name: makeDirtyStates(false) },
        } as unknown as WidgetDirtyStates;

        const pruned = pruneResourceData(
            resourceData,
            widgetDirtyStates,
            new Set<string>(),
        );

        expect(Object.keys(pruned.aliased_data)).toEqual([]);
    });

    it("keeps persisted tiles in a cardinality-n list while dropping an untouched placeholder", () => {
        const resourceData = makeResourceData({
            name: [
                makeTile(PERSISTED_TILE_ID),
                makeTile(CLIENT_GENERATED_TILE_ID),
            ],
        });
        const widgetDirtyStates = {
            aliased_data: {
                name: [makeDirtyStates(false), makeDirtyStates(false)],
            },
        } as unknown as WidgetDirtyStates;

        const pruned = pruneResourceData(
            resourceData,
            widgetDirtyStates,
            new Set([CLIENT_GENERATED_TILE_ID]),
        );

        expect(pruned.aliased_data.name).toEqual([
            expect.objectContaining({ tileid: PERSISTED_TILE_ID }),
        ]);
    });

    it("omits the alias when a cardinality-n list is emptied, so the server deletes its tiles", () => {
        const resourceData = makeResourceData({ name: [] });
        const widgetDirtyStates = {
            aliased_data: { name: [] },
        } as unknown as WidgetDirtyStates;

        const pruned = pruneResourceData(
            resourceData,
            widgetDirtyStates,
            new Set<string>(),
        );

        expect(Object.keys(pruned.aliased_data)).toEqual([]);
    });
});
