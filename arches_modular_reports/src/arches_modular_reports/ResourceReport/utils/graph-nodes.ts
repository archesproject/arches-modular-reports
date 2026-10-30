import type { NodegroupWidgetConfig } from "@/arches_vue_components/types.ts";
import type { GraphNode } from "@/arches_modular_reports/ResourceReport/types.ts";

export function indexGraphNodes(
    nodegroupWidgetConfigs: Record<string, NodegroupWidgetConfig>,
): Record<string, GraphNode> {
    const graphNodesByAlias: Record<string, GraphNode> = {};
    for (const [nodegroupAlias, nodegroupWidgetConfig] of Object.entries(
        nodegroupWidgetConfigs,
    )) {
        for (const widget of nodegroupWidgetConfig.card_x_node_x_widgets) {
            graphNodesByAlias[widget.node.alias] = {
                label: widget.label,
                nodegroupAlias,
            };
        }
    }
    return graphNodesByAlias;
}

export function nodegroupLineage(
    nodegroupWidgetConfigs: Record<string, NodegroupWidgetConfig>,
    nodegroupAlias: string,
): string[] {
    const lineage: string[] = [];
    let currentAlias: string | null = nodegroupAlias;
    while (currentAlias !== null && currentAlias in nodegroupWidgetConfigs) {
        lineage.push(currentAlias);
        currentAlias =
            nodegroupWidgetConfigs[currentAlias].parent_nodegroup_alias;
    }
    return lineage;
}

export function childNodegroupAliases(
    nodegroupWidgetConfigs: Record<string, NodegroupWidgetConfig>,
    nodegroupAlias: string | null,
): string[] {
    return Object.entries(nodegroupWidgetConfigs)
        .filter(
            ([, nodegroupWidgetConfig]) =>
                nodegroupWidgetConfig.parent_nodegroup_alias ===
                    nodegroupAlias && nodegroupWidgetConfig.card?.visible,
        )
        .sort(
            ([, firstConfig], [, secondConfig]) =>
                (firstConfig.card?.sortorder ?? 0) -
                (secondConfig.card?.sortorder ?? 0),
        )
        .map(([childNodegroupAlias]) => childNodegroupAlias);
}
