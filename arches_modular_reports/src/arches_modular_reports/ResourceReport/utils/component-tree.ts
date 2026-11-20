import { localizeLabel } from "@/arches_modular_reports/ResourceReport/utils/localize-label.ts";

import type { NodegroupWidgetConfig } from "@/arches_vue_components/types.ts";
import type {
    ComponentNode,
    FolioConfig,
    LabelledConfig,
    ReportTabGroup,
} from "@/arches_modular_reports/ResourceReport/types.ts";

const REPORT_TABS_COMPONENT =
    "arches_modular_reports/ResourceReport/components/ReportTabs";

type TreeNode = ComponentNode<
    LabelledConfig & FolioConfig & Record<string, unknown>
>;

export function isComponentNode(value: unknown): value is TreeNode {
    return (
        typeof value === "object" &&
        value !== null &&
        "component" in value &&
        "config" in value
    );
}

export function childNodes(node: ComponentNode<object>): TreeNode[] {
    return Object.values(node.config).flatMap((configValue) => {
        if (Array.isArray(configValue)) {
            return configValue.filter(isComponentNode);
        }
        return [];
    });
}

function descendantNodes(nodes: ComponentNode<object>[]): TreeNode[] {
    return nodes
        .filter(isComponentNode)
        .flatMap((node) => [node, ...descendantNodes(childNodes(node))]);
}

export function componentPaths(nodes: ComponentNode<object>[]): string[] {
    return [...new Set(descendantNodes(nodes).map((node) => node.component))];
}

export function containsFolios(node: ComponentNode<object>): boolean {
    return nodegroupAliasesWithin(node).size > 0;
}

export function withoutHiddenCards<TNode extends ComponentNode<object>>(
    nodes: TNode[],
    nodegroupWidgetConfigs: Record<string, NodegroupWidgetConfig>,
): TNode[] {
    return nodes
        .filter((node) => !isHiddenNode(node, nodegroupWidgetConfigs))
        .map((node) => withoutHiddenChildren(node, nodegroupWidgetConfigs));
}

function withoutHiddenChildren<TNode extends ComponentNode<object>>(
    node: TNode,
    nodegroupWidgetConfigs: Record<string, NodegroupWidgetConfig>,
): TNode {
    if (!isComponentNode(node)) {
        return node;
    }
    const config = Object.fromEntries(
        Object.entries(node.config).map(([configKey, configValue]) => [
            configKey,
            withoutHiddenCardsIn(configValue, nodegroupWidgetConfigs),
        ]),
    );
    return { ...node, config };
}

function withoutHiddenCardsIn(
    configValue: unknown,
    nodegroupWidgetConfigs: Record<string, NodegroupWidgetConfig>,
): unknown {
    if (Array.isArray(configValue) && configValue.some(isComponentNode)) {
        return withoutHiddenCards(configValue, nodegroupWidgetConfigs);
    }
    return configValue;
}

function isHiddenNode(
    node: ComponentNode<object>,
    nodegroupWidgetConfigs: Record<string, NodegroupWidgetConfig>,
): boolean {
    if (!isComponentNode(node)) {
        return false;
    }
    const { nodegroup_alias: nodegroupAlias } = node.config;
    if (typeof nodegroupAlias === "string") {
        return nodegroupWidgetConfigs[nodegroupAlias]?.card?.visible === false;
    }
    const children = childNodes(node);
    return (
        children.length > 0 &&
        children.every((child) => isHiddenNode(child, nodegroupWidgetConfigs))
    );
}

export function nodegroupAliasesWithin(
    node: ComponentNode<object>,
): Set<string> {
    const nodegroupAliases = new Set<string>();
    for (const descendantNode of descendantNodes([node])) {
        const { nodegroup_alias: nodegroupAlias } = descendantNode.config;
        if (typeof nodegroupAlias === "string") {
            nodegroupAliases.add(nodegroupAlias);
        }
    }
    return nodegroupAliases;
}

export function reportTabGroups(
    nodes: ComponentNode<object>[],
    activeLanguage: string,
    defaultLanguage: string,
): ReportTabGroup[] {
    const placedNodegroupAliases = new Set<string>();
    return descendantNodes(nodes)
        .filter((node) => node.component === REPORT_TABS_COMPONENT)
        .flatMap(childNodes)
        .map((tabNode) => {
            const nodegroupAliases = [
                ...nodegroupAliasesWithin(tabNode),
            ].filter(
                (nodegroupAlias) => !placedNodegroupAliases.has(nodegroupAlias),
            );
            nodegroupAliases.forEach((nodegroupAlias) =>
                placedNodegroupAliases.add(nodegroupAlias),
            );
            return {
                label: localizeLabel(
                    tabNode.config.label ?? null,
                    activeLanguage,
                    defaultLanguage,
                ),
                nodegroupAliases,
            };
        });
}

export function folioLocations(
    nodes: ComponentNode<object>[],
    activeLanguage: string,
    defaultLanguage: string,
): Record<string, string> {
    const locationsByNodegroupAlias: Record<string, string> = {};

    function visit(node: TreeNode, ancestorLabels: string[]): void {
        if (node.config.nodegroup_alias !== undefined) {
            locationsByNodegroupAlias[node.config.nodegroup_alias] ??=
                ancestorLabels.join(" / ");
        }
        const label = localizeLabel(
            node.config.label ?? null,
            activeLanguage,
            defaultLanguage,
        );
        const labels =
            label === "" ? ancestorLabels : [...ancestorLabels, label];
        for (const childNode of childNodes(node)) {
            visit(childNode, labels);
        }
    }

    for (const node of nodes.filter(isComponentNode)) {
        visit(node, []);
    }
    return locationsByNodegroupAlias;
}
