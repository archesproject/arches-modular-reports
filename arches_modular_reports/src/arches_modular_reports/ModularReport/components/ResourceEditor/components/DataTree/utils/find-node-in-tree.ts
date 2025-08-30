import type { TreeNode } from "primevue/treenode";

function childrenOf(cursor: TreeNode[] | TreeNode | null): TreeNode[] {
    if (Array.isArray(cursor)) {
        return cursor;
    }

    if (cursor === null) {
        return [];
    }

    if (Array.isArray(cursor.children)) {
        return cursor.children as TreeNode[];
    }

    return [];
}

function getAlias(node: TreeNode): string | undefined {
    const nodeData = node.data;

    if (nodeData === null || nodeData === undefined) {
        return undefined;
    }

    return nodeData.alias;
}

export function findNodeInTree(
    rootNodes: TreeNode[],
    pathWithAliasedData: Array<string | number>,
): { foundNode: TreeNode | null; nodePath: TreeNode[] } {
    const cleanedPath = pathWithAliasedData.filter(
        (segment) => segment !== "aliased_data",
    );

    let currentCursor: TreeNode[] | TreeNode | null = rootNodes;
    const nodePath: TreeNode[] = [];
    let previousAlias: string | undefined = undefined;

    let segmentIndex = 0;
    while (segmentIndex < cleanedPath.length) {
        if (currentCursor === null) {
            break;
        }

        const candidateChildren = childrenOf(currentCursor);
        const currentSegment = cleanedPath[segmentIndex];

        if (typeof currentSegment === "string") {
            const matchedNode =
                candidateChildren.find(
                    (candidateNode) =>
                        getAlias(candidateNode) === currentSegment,
                ) || null;

            if (matchedNode === null) {
                currentCursor = null;
                break;
            }

            currentCursor = matchedNode;
            nodePath.push(matchedNode);
            previousAlias = currentSegment;
            segmentIndex += 1;
            continue;
        }

        if (typeof currentSegment === "number") {
            if (typeof previousAlias !== "string") {
                currentCursor = null;
                break;
            }

            const siblingsWithSameAlias = candidateChildren.filter(
                (candidateNode) => getAlias(candidateNode) === previousAlias,
            );

            if (currentSegment < 0) {
                currentCursor = null;
                break;
            }
            if (currentSegment >= siblingsWithSameAlias.length) {
                currentCursor = null;
                break;
            }

            const matchedIndexedNode = siblingsWithSameAlias[currentSegment];
            currentCursor = matchedIndexedNode;
            nodePath.push(matchedIndexedNode);
            segmentIndex += 1;
            continue;
        }

        currentCursor = null;
        break;
    }

    let foundNode: TreeNode | null = null;
    if (currentCursor !== null) {
        if (!Array.isArray(currentCursor)) {
            foundNode = currentCursor;
        }
    }

    let ancestorPathExcludingFound: TreeNode[] = [];
    if (foundNode !== null) {
        ancestorPathExcludingFound = nodePath.slice(0, -1);
    }

    return { foundNode, nodePath: ancestorPathExcludingFound };
}
