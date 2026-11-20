import { isAliasedNodeData } from "@/arches_vue_components/generics/GenericCard/utils.ts";

import {
    nodeHasData,
    nodeSearchTexts,
    nodeText,
} from "@/arches_modular_reports/ResourceReport/utils/localized-text.ts";

import type {
    AliasedNodeData,
    AliasedNodegroupData,
    AliasedTileData,
    NodegroupWidgetConfig,
} from "@/arches_vue_components/types.ts";
import type {
    NodeTextContext,
    ResourceChangeSet,
} from "@/arches_modular_reports/ResourceReport/types.ts";

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

export function containsTile(tile: AliasedTileData, tileId: string): boolean {
    if (tile.tileid === tileId) {
        return true;
    }
    return Object.values(tile.aliased_data).some((value) =>
        nodegroupTiles(value).some((childTile) =>
            containsTile(childTile, tileId),
        ),
    );
}

export function tileHasData(
    tile: AliasedTileData,
    context: NodeTextContext,
): boolean {
    return Object.entries(tile.aliased_data).some(([alias, value]) => {
        if (isAliasedNodeData(value)) {
            return nodeHasData(alias, value, context);
        }
        return nodegroupTiles(value).some((childTile) =>
            tileHasData(childTile, context),
        );
    });
}

export function tileSearchText(
    tile: AliasedTileData,
    context: NodeTextContext,
): string {
    const displayValues: string[] = [];

    function visit(currentTile: AliasedTileData): void {
        for (const [alias, value] of Object.entries(currentTile.aliased_data)) {
            if (isAliasedNodeData(value)) {
                displayValues.push(...nodeSearchTexts(alias, value, context));
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
    context: NodeTextContext,
): string {
    const summaryValues: string[] = [];
    const summaryWidgets = nodegroupWidgetConfig.card_x_node_x_widgets
        .filter((widget) => widget.visible)
        .slice(0, SUMMARY_FIELD_COUNT);
    for (const widget of summaryWidgets) {
        const valueText = nodeText(
            widget.node.alias,
            aliasedNodeDataOf(tile, widget.node.alias),
            context,
        );
        if (valueText.trim() !== "") {
            summaryValues.push(valueText);
        }
    }
    return summaryValues.join(" · ");
}
