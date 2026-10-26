import { computed, onMounted, onUnmounted, useTemplateRef } from "vue";

import { useReportData } from "@/arches_modular_reports/ResourceReport/composables/useReportData.ts";
import {
    canAddTile,
    nodegroupTiles,
    tileSummary,
} from "@/arches_modular_reports/ResourceReport/utils/tiles.ts";

import type { ComputedRef } from "vue";
import type {
    AliasedTileData,
    NodegroupWidgetConfig,
} from "@/arches_vue_components/types.ts";
import type {
    ComponentNode,
    FolioConfig,
    ReportData,
} from "@/arches_modular_reports/ResourceReport/types.ts";

export type SavedTile = AliasedTileData & { tileid: string };

export interface Folio {
    reportData: ComputedRef<ReportData>;
    nodegroupAlias: ComputedRef<string>;
    hasNodegroup: ComputedRef<boolean>;
    nodegroupWidgetConfig: ComputedRef<NodegroupWidgetConfig>;
    cardName: ComputedRef<string>;
    parentTileId: ComputedRef<string | null>;
    isNested: ComputedRef<boolean>;
    tiles: ComputedRef<AliasedTileData[]>;
    isAddable: ComputedRef<boolean>;
    isFlashed: ComputedRef<boolean>;
    isEditableTile: (tile: AliasedTileData) => tile is SavedTile;
    tileLabel: (tile: AliasedTileData) => string;
    addTile: () => Promise<void>;
    editTile: (tileId: string) => void;
    deleteTile: (tileId: string) => void;
    clearFlash: () => void;
}

export function useFolio(
    component: () => ComponentNode<FolioConfig>,
    parentTile: () => AliasedTileData | null = () => null,
): Folio {
    const reportData = useReportData();
    const folioElement = useTemplateRef<HTMLElement>("folio");

    const nodegroupAlias = computed(
        () => component().config.nodegroup_alias ?? "",
    );

    const hasNodegroup = computed(
        () => nodegroupAlias.value in reportData.value.nodegroupWidgetConfigs,
    );

    const nodegroupWidgetConfig = computed(
        () => reportData.value.nodegroupWidgetConfigs[nodegroupAlias.value],
    );

    const cardName = computed(
        () => nodegroupWidgetConfig.value.card?.name ?? "",
    );

    const parentTileId = computed(() => parentTile()?.tileid ?? null);

    const isNested = computed(() => parentTile() !== null);

    const tiles = computed(() => {
        const parent = parentTile();
        if (parent === null) {
            return nodegroupTiles(
                reportData.value.resource.aliased_data[nodegroupAlias.value],
            );
        }
        return nodegroupTiles(parent.aliased_data[nodegroupAlias.value]);
    });

    const canEditEntries = computed(
        () => reportData.value.canEdit && reportData.value.editor.isAvailable,
    );

    const isAddable = computed(
        () =>
            canEditEntries.value &&
            canAddTile(
                nodegroupWidgetConfig.value,
                tiles.value.length,
                parentTileId.value,
                reportData.value.changeSet,
            ),
    );

    const isFlashed = computed(
        () =>
            reportData.value.folioNavigation.flashedNodegroupAlias.value ===
            nodegroupAlias.value,
    );

    let unregisterFolio = (): void => undefined;

    onMounted(() => {
        if (
            folioElement.value !== null &&
            hasNodegroup.value &&
            !isNested.value
        ) {
            unregisterFolio = reportData.value.folioNavigation.registerFolio(
                nodegroupAlias.value,
                folioElement.value,
            );
        }
    });

    onUnmounted(() => {
        unregisterFolio();
    });

    function isEditableTile(tile: AliasedTileData): tile is SavedTile {
        return (
            canEditEntries.value &&
            nodegroupWidgetConfig.value.is_writable &&
            tile.tileid !== null &&
            !reportData.value.changeSet.isPendingDelete(tile.tileid)
        );
    }

    function tileLabel(tile: AliasedTileData): string {
        const summary = tileSummary(tile, nodegroupWidgetConfig.value);
        if (summary === "") {
            return cardName.value;
        }
        return summary;
    }

    async function addTile(): Promise<void> {
        const tileId = await reportData.value.changeSet.addTile(
            nodegroupAlias.value,
            parentTileId.value,
        );
        if (tileId !== null) {
            reportData.value.editor.open({
                nodegroupAlias: nodegroupAlias.value,
                tileId,
            });
        }
    }

    function editTile(tileId: string): void {
        reportData.value.editor.open({
            nodegroupAlias: nodegroupAlias.value,
            tileId,
        });
    }

    function deleteTile(tileId: string): void {
        reportData.value.changeSet.deleteTile(nodegroupAlias.value, tileId);
    }

    function clearFlash(): void {
        reportData.value.folioNavigation.clearFlash();
    }

    return {
        reportData,
        nodegroupAlias,
        hasNodegroup,
        nodegroupWidgetConfig,
        cardName,
        parentTileId,
        isNested,
        tiles,
        isAddable,
        isFlashed,
        isEditableTile,
        tileLabel,
        addTile,
        editTile,
        deleteTile,
        clearFlash,
    };
}
