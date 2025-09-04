import type { TreeNode } from "primevue/treenode";
import type { ResourceData } from "@/arches_modular_reports/ModularReport/types";

function findTreePathByKey(
    rootNodes: TreeNode[],
    targetKey: string | number,
): TreeNode[] | null {
    for (const node of rootNodes) {
        if (node.key === targetKey) {
            return [node];
        }
        if (Array.isArray(node.children)) {
            const path = findTreePathByKey(node.children, targetKey);
            if (path) {
                return [node, ...path];
            }
        }
    }
    return null;
}

function resolveArrayIndex(
    tiles: unknown,
    parentNode: TreeNode,
    childNode: TreeNode | undefined,
): number {
    if (!childNode || !Array.isArray(tiles)) {
        return 0;
    }

    const siblings = parentNode.children ?? [];
    const indexByTree = siblings.indexOf(childNode);
    if (indexByTree >= 0) {
        return indexByTree;
    }

    if (childNode.data?.tileid) {
        const indexByTileId = tiles.findIndex(
            (tile) => tile?.tileid === childNode.data?.tileid,
        );

        if (indexByTileId >= 0) {
            return indexByTileId;
        }
    }

    return 0;
}

export function generateTilePath(
    resourceData: ResourceData,
    treeRoots: TreeNode[],
    selectedKey: string | number,
): Array<string | number> {
    const pathNodes = findTreePathByKey(treeRoots, selectedKey);
    if (!pathNodes) {
        return [];
    }

    const segments: Array<string | number> = ["aliased_data"];
    let pointer: Record<string, unknown> | undefined =
        resourceData.aliased_data;

    for (const [pathIndex, currentNode] of pathNodes.entries()) {
        let parentNode;
        if (pathIndex > 0) {
            parentNode = pathNodes[pathIndex - 1];
        }

        let nextNode;
        if (pathIndex + 1 < pathNodes.length) {
            nextNode = pathNodes[pathIndex + 1];
        }

        if (!("nodegroupAlias" in currentNode.data)) {
            if (
                currentNode.data?.alias &&
                parentNode?.data?.alias !== currentNode.data?.alias
            ) {
                segments.push(currentNode.data?.alias);

                if (pointer && !Array.isArray(pointer)) {
                    pointer = pointer[currentNode.data?.alias] as Record<
                        string,
                        unknown
                    >;
                }
            }

            if (Array.isArray(pointer) && nextNode) {
                const arrayIndex = resolveArrayIndex(
                    pointer,
                    currentNode,
                    nextNode,
                );
                segments.push(arrayIndex);
                pointer = pointer[arrayIndex];
            }

            if ("aliased_data" in pointer!) {
                segments.push("aliased_data");
                pointer = pointer.aliased_data as Record<string, unknown>;
            }

            continue;
        }

        if (currentNode.data?.alias) {
            segments.push(currentNode.data?.alias);
        }
        break;
    }

    return segments;
}
