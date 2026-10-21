import { childNodegroupAliases } from "@/arches_modular_reports/ResourceReport/utils/graph-nodes.ts";
import { tileSearchText } from "@/arches_modular_reports/ResourceReport/utils/tiles.ts";

import type {
    AliasedTileData,
    NodegroupWidgetConfig,
} from "@/arches_vue_components/types.ts";

export function ownLabelsMatch(
    nodegroupWidgetConfig: NodegroupWidgetConfig,
    query: string,
): boolean {
    const labels = [
        nodegroupWidgetConfig.card?.name ?? "",
        ...nodegroupWidgetConfig.card_x_node_x_widgets
            .filter((widget) => widget.visible)
            .map((widget) => widget.label),
    ];
    return labels.some((label) => label.toLocaleLowerCase().includes(query));
}

export function nodegroupMatches(
    nodegroupWidgetConfigs: Record<string, NodegroupWidgetConfig>,
    nodegroupAlias: string,
    query: string,
): boolean {
    return (
        ownLabelsMatch(nodegroupWidgetConfigs[nodegroupAlias], query) ||
        childNodegroupAliases(nodegroupWidgetConfigs, nodegroupAlias).some(
            (childAlias) =>
                nodegroupMatches(nodegroupWidgetConfigs, childAlias, query),
        )
    );
}

export function folioMatches(
    nodegroupWidgetConfigs: Record<string, NodegroupWidgetConfig>,
    nodegroupAlias: string,
    tiles: AliasedTileData[],
    query: string,
): boolean {
    return (
        nodegroupMatches(nodegroupWidgetConfigs, nodegroupAlias, query) ||
        tiles.some((tile) => tileSearchText(tile).includes(query))
    );
}
