import { isAliasedNodeData } from "@/arches_vue_components/generics/GenericCard/utils.ts";

import type {
    AliasedNodeData,
    AliasedNodegroupData,
    AliasedTileData,
    NodegroupWidgetConfig,
} from "@/arches_vue_components/types.ts";

const SUMMARY_FIELD_COUNT = 2;

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
): boolean {
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
        const nodeData = tile.aliased_data[widget.node.alias];
        if (isAliasedNodeData(nodeData) && nodeData.display_value) {
            summaryValues.push(nodeData.display_value);
        }
    }
    return summaryValues.join(" · ");
}
