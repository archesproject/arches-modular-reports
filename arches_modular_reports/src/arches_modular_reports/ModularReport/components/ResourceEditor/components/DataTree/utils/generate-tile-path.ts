import type { TreeNode } from "primevue/treenode";
import type { ResourceData } from "@/arches_modular_reports/ModularReport/types";

function findTreePathByKey(
    rootNodes: TreeNode[],
    targetKey: string | number,
): TreeNode[] | null {
    for (const rootNode of rootNodes) {
        if (rootNode.key === targetKey) {
            return [rootNode];
        }
        if (rootNode.children?.length) {
            const descendantPath = findTreePathByKey(
                rootNode.children,
                targetKey,
            );
            if (descendantPath) {
                return [rootNode, ...descendantPath];
            }
        }
    }
    return null;
}

function resolveArrayIndex(
    arrayValue: unknown,
    parentNode: TreeNode,
    childNode: TreeNode | undefined,
): number {
    const fallbackIndex = 0;

    if (!Array.isArray(arrayValue) || !childNode) {
        return fallbackIndex;
    }

    const siblings = parentNode.children ?? [];
    const indexFromTree = siblings.findIndex(
        (candidate) => candidate === childNode,
    );
    if (indexFromTree >= 0) {
        return indexFromTree;
    }

    let childTileId: string | null | undefined;
    if (
        childNode.data &&
        typeof childNode.data === "object" &&
        "tileid" in childNode.data
    ) {
        const possible = (childNode.data as { tileid?: unknown }).tileid;
        childTileId =
            typeof possible === "string"
                ? possible
                : possible === null
                  ? null
                  : undefined;
    } else {
        childTileId = undefined;
    }

    if (childTileId) {
        const array = arrayValue as unknown[];
        const indexFromTileId = array.findIndex((tileObject) => {
            if (
                tileObject &&
                typeof tileObject === "object" &&
                "tileid" in tileObject
            ) {
                const candidate = (tileObject as { tileid?: unknown }).tileid;
                return candidate === childTileId;
            }
            return false;
        });
        if (indexFromTileId >= 0) {
            return indexFromTileId;
        }
    }

    return (arrayValue as unknown[]).length === 1 ? 0 : fallbackIndex;
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

    const jsonPathSegments: Array<string | number> = ["aliased_data"];

    let currentPointer: unknown;
    if (
        resourceData &&
        typeof resourceData === "object" &&
        "aliased_data" in resourceData
    ) {
        currentPointer = (resourceData as { aliased_data?: unknown })
            .aliased_data;
    } else {
        currentPointer = undefined;
    }

    for (let nodeIndex = 0; nodeIndex < pathNodes.length; nodeIndex += 1) {
        const currentNode = pathNodes[nodeIndex];
        const parentNode = pathNodes[nodeIndex - 1];
        const nextNode = pathNodes[nodeIndex + 1];

        const currentData = currentNode.data;
        const isLeafNode = !!(
            currentData &&
            typeof currentData === "object" &&
            "nodegroupAlias" in currentData
        );

        let currentAlias: string | undefined;
        if (
            currentData &&
            typeof currentData === "object" &&
            "alias" in currentData
        ) {
            const possibleAlias = (currentData as { alias?: unknown }).alias;
            currentAlias =
                typeof possibleAlias === "string" ? possibleAlias : undefined;
        } else {
            currentAlias = undefined;
        }

        if (!isLeafNode) {
            let parentAlias: string | undefined;
            if (
                parentNode?.data &&
                typeof parentNode.data === "object" &&
                "alias" in parentNode.data
            ) {
                const possibleParentAlias = (
                    parentNode.data as { alias?: unknown }
                ).alias;
                parentAlias =
                    typeof possibleParentAlias === "string"
                        ? possibleParentAlias
                        : undefined;
            } else {
                parentAlias = undefined;
            }

            const shouldPushAlias = !parentNode || parentAlias !== currentAlias;

            if (shouldPushAlias && currentAlias) {
                jsonPathSegments.push(currentAlias);
                if (
                    currentPointer &&
                    typeof currentPointer === "object" &&
                    currentAlias in (currentPointer as Record<string, unknown>)
                ) {
                    currentPointer = (
                        currentPointer as Record<string, unknown>
                    )[currentAlias];
                } else {
                    currentPointer = undefined;
                }
            }

            if (Array.isArray(currentPointer) && nextNode) {
                const indexWithinArray = resolveArrayIndex(
                    currentPointer,
                    currentNode,
                    nextNode,
                );
                jsonPathSegments.push(indexWithinArray);
                currentPointer = currentPointer[indexWithinArray];
            }

            if (
                currentPointer &&
                typeof currentPointer === "object" &&
                "aliased_data" in currentPointer
            ) {
                jsonPathSegments.push("aliased_data");
                currentPointer = (currentPointer as { aliased_data?: unknown })
                    .aliased_data;
            }

            continue;
        }

        if (currentAlias) {
            jsonPathSegments.push(currentAlias);
        }
        break;
    }

    return jsonPathSegments;
}
