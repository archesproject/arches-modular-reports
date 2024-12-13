import { defineAsyncComponent } from "vue";

import type {
    ComponentLookup,
    NamedSection,
    SectionContent,
    Tile,
    TileValue,
} from "@/arches_provenance/EditableReport/types";

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
            componentLookup[component.component] = defineAsyncComponent(() =>
                import(
                    `@/arches_provenance/EditableReport/components/${component.component}.vue`
                ).catch(
                    () =>
                        import(
                            `@/arches_provenance/EditableReport/components/${component.component}/${component.component}.vue`
                        ),
                ),
            );
        });
    });
}

export function findNodeValue(
    labelBasedResource: { resource: Tile },
    nodeAlias: string,
): TileValue | undefined {
    function searchSiblingNodes(tile: Tile): TileValue | undefined {
        for (const [tileNodeAlias, tileData] of Object.entries(tile)) {
            if (tileNodeAlias === nodeAlias) {
                return tileData;
            }
            if (tileData instanceof Array) {
                for (const childTile of tileData) {
                    const searchResult = searchSiblingNodes(childTile);
                    if (searchResult) {
                        return searchResult;
                    }
                }
            }
        }
    }
    return searchSiblingNodes(labelBasedResource.resource);
}
