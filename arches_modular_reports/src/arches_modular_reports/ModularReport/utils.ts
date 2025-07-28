import { defineAsyncComponent } from "vue";

import type { TreeNode } from "primevue/treenode";
import type {
    ComponentLookup,
    NamedSection,
    NodeValueDisplayData,
    SectionContent,
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

    function recurse(items: TreeNode[]): TreeNode | undefined {
        for (const item of items) {
            if (tileId && item.data.tileid === tileId) {
                return item;
            }
            if (!tileId && item.data.alias === nodegroupAlias) {
                // Wrapper nodes for top cards
                return item;
            }
            if (item.children) {
                for (const child of item.children) {
                    const found = recurse([child]);
                    if (found) {
                        path.push(item);
                        return found;
                    }
                }
            }
        }
    }

    const found = recurse(tree);
    if (!found) {
        throw new Error();
    }

    return { found, path };
}
