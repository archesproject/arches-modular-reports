import { isAliasedNodeData } from "@/arches_vue_components/generics/GenericCard/utils.ts";

import type {
    AliasedNodeData,
    AliasedNodegroupData,
    AliasedTileData,
    NodegroupWidgetConfig,
} from "@/arches_vue_components/types.ts";
import type { ResourceChangeSet } from "@/arches_modular_reports/ResourceReport/types.ts";

const SUMMARY_FIELD_COUNT = 2;

export function aliasedNodeDataOf(
    tile: AliasedTileData,
    nodeAlias: string,
): AliasedNodeData | null {
    const nodeData = tile.aliased_data[nodeAlias];
    if (isAliasedNodeData(nodeData)) {
        return nodeData;
    }
    return null;
}

export function nodegroupTiles(
    nodegroupData: AliasedNodeData | AliasedNodegroupData | undefined,
): AliasedTileData[] {
    if (Array.isArray(nodegroupData)) {
        return [...nodegroupData].sort(
            (firstTile, secondTile) =>
                firstTile.sortorder - secondTile.sortorder,
        );
    }
    if (nodegroupData && !isAliasedNodeData(nodegroupData)) {
        return [nodegroupData];
    }
    return [];
}

export function tileSearchText(tile: AliasedTileData): string {
    const displayValues: string[] = [];

    function visit(currentTile: AliasedTileData): void {
        for (const value of Object.values(currentTile.aliased_data)) {
            if (isAliasedNodeData(value)) {
                displayValues.push(value.display_value);
            } else {
                nodegroupTiles(value).forEach(visit);
            }
        }
    }

    visit(tile);
    return displayValues.join(" ").toLocaleLowerCase();
}

export function canAddTile(
    nodegroupWidgetConfig: NodegroupWidgetConfig,
    existingTileCount: number,
    parentTileId: string | null,
    changeSet: ResourceChangeSet,
): boolean {
    if (parentTileId !== null && changeSet.isPendingDelete(parentTileId)) {
        return false;
    }
    return (
        nodegroupWidgetConfig.is_writable &&
        (nodegroupWidgetConfig.cardinality === "n" || existingTileCount === 0)
    );
}

export function tileSummary(
    tile: AliasedTileData,
    nodegroupWidgetConfig: NodegroupWidgetConfig,
): string {
    const summaryValues: string[] = [];
    const summaryWidgets = nodegroupWidgetConfig.card_x_node_x_widgets
        .filter((widget) => widget.visible)
        .slice(0, SUMMARY_FIELD_COUNT);
    for (const widget of summaryWidgets) {
        const displayValue = aliasedNodeDataOf(
            tile,
            widget.node.alias,
        )?.display_value;
        if (displayValue) {
            summaryValues.push(displayValue);
        }
    }
    return summaryValues.join(" · ");
}
