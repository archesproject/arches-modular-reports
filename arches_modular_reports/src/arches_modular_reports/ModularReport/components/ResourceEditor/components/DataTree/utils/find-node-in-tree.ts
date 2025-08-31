import type { TreeNode } from "primevue/treenode";

export function findNodeInTree(
    rootNodes: TreeNode[],
    path: Array<string | number>,
) {
    let currentLevelNodes = rootNodes;
    const traversedPath = [];
    let previousAliasForIndex: string | undefined;

    for (const currentSegment of path.filter(
        (segment) => segment !== "aliased_data",
    )) {
        let matchedNode;

        if (typeof currentSegment === "string") {
            matchedNode = currentLevelNodes.find(
                (candidateNode) => candidateNode.data?.alias === currentSegment,
            );
            previousAliasForIndex = currentSegment;
        }

        if (typeof currentSegment === "number") {
            const siblings = currentLevelNodes.filter(
                (candidateNode) =>
                    candidateNode.data?.alias === previousAliasForIndex,
            );
            matchedNode = siblings[currentSegment];
        }

        if (!matchedNode) {
            break;
        }

        traversedPath.push(matchedNode);
        currentLevelNodes = Array.isArray(matchedNode.children)
            ? matchedNode.children
            : [];
    }

    return {
        foundNode: traversedPath.at(-1),
        nodePath: traversedPath.slice(0, -1),
    };
}
