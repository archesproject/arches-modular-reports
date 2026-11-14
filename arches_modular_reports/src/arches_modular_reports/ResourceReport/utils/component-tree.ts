import { localizeLabel } from "@/arches_modular_reports/ResourceReport/utils/localize-label.ts";

import type {
    ComponentNode,
    FolioConfig,
    LabelledConfig,
    ReportTabGroup,
} from "@/arches_modular_reports/ResourceReport/types.ts";

const REPORT_TABS_COMPONENT_NAME = "ReportTabs";

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

// Every tab of every ReportTabs in the tree, in report order, each with the
// nodegroups it shows. A nodegroup shown in more than one tab belongs to the
// first.
export function reportTabGroups(
    nodes: ComponentNode<object>[],
    activeLanguage: string,
): ReportTabGroup[] {
    const placedNodegroupAliases = new Set<string>();
    return descendantNodes(nodes)
        .filter(
            (node) =>
                node.component.split("/").at(-1) === REPORT_TABS_COMPONENT_NAME,
        )
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
                ),
                nodegroupAliases,
            };
        });
}

export function folioLocations(
    nodes: ComponentNode<object>[],
    activeLanguage: string,
): Record<string, string> {
    const locationsByNodegroupAlias: Record<string, string> = {};

    function visit(node: TreeNode, ancestorLabels: string[]): void {
        if (node.config.nodegroup_alias !== undefined) {
            locationsByNodegroupAlias[node.config.nodegroup_alias] ??=
                ancestorLabels.join(" / ");
        }
        const label = localizeLabel(node.config.label ?? null, activeLanguage);
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
