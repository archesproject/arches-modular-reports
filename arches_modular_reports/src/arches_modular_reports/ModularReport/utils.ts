import { defineAsyncComponent } from "vue";

import type { TreeNode } from "primevue/treenode";
import type {
    ComponentLookup,
    NamedSection,
    NodeValueDisplayData,
    SectionContent,
    ResourceData,
    TileData,
} from "@/arches_modular_reports/ModularReport/types";

export function uniqueId(_unused: unknown) {
    /* Not cryptographically secure, but good enough for Vue component keys. */
    return Math.floor(Math.random() * Date.now());
}

export async function importComponents(
    namedSections: NamedSection[],
    componentLookup: ComponentLookup,
): Promise<void> {
    namedSections.forEach((section: NamedSection) => {
        section.components.forEach((component: SectionContent) => {
            componentLookup[component.component] = {
                component: defineAsyncComponent(
                    () => import(`@/${component.component}.vue`),
                ),
                key: uniqueId(component),
            };
        });
    });
}

export function truncateDisplayData(
    displayValues: NodeValueDisplayData[],
    limit: number,
) {
    // The tiles were already fetched with a limit, but we unpack
    // multiple display values for *-list datatypes, so truncate.
    let counter = 0;
    return displayValues.reduce((acc, tileData) => {
        counter += tileData.display_values.length;
        const excess = counter - limit;
        if (excess > 0) {
            acc.push({
                display_values: tileData.display_values.slice(0, -excess),
                links: tileData.links.slice(0, -excess),
            });
        } else {
            acc.push(tileData);
        }
        return acc;
    }, [] as NodeValueDisplayData[]);
}

// a riff on the version from arches-controlled-lists using different attributes
export function findNodeInTree(
    tree: TreeNode[],
    tileId: string | null,
    nodegroupAlias: string | undefined,
) {
    const path: TreeNode[] = [];

    const matches = (node: TreeNode) => {
        if (tileId) {
            return node.data.tileid === tileId;
        }
        return node.data.alias === nodegroupAlias;
    };

    function recurse(nodes: TreeNode[]): TreeNode | undefined {
        for (const currentNode of nodes) {
            if (matches(currentNode)) {
                return currentNode;
            }
            const childNodes = currentNode.children;
            if (childNodes?.length) {
                const foundInChildren = recurse(childNodes);
                if (foundInChildren) {
                    path.push(currentNode);
                    return foundInChildren;
                }
            }
        }
        return undefined;
    }

    const found = recurse(tree);
    if (!found) {
        throw new Error();
    }

    return { found, path };
}

export function findTileInTileTree(
    resourceOrTileData: ResourceData | TileData,
    tileId: string,
) {
    function traverse(
        resourceOrTileData: ResourceData | TileData,
    ): TileData | undefined {
        if ((resourceOrTileData as TileData).tileid === tileId) {
            return resourceOrTileData as TileData;
        }
        for (const data of Object.values(resourceOrTileData.aliased_data)) {
            let found;
            if (Array.isArray(data)) {
                for (const tileData of data) {
                    found = traverse(tileData);
                    if (found) {
                        return found;
                    }
                }
            } else if ((data as TileData)?.aliased_data) {
                found = traverse(data as TileData);
                if (found) {
                    return found;
                }
            }
        }
    }

    const found = traverse(resourceOrTileData);
    if (!found) {
        throw new Error();
    }
    return found;
}
