import { defineAsyncComponent } from "vue";

import type {
    ComponentLookup,
    NamedSection,
    SectionContent,
    Tile,
    TileValue,
} from "@/arches_provenance/EditableReport/types";

export async function importComponents(
    namedSections: NamedSection[],
    componentLookup: ComponentLookup,
): Promise<void> {
    namedSections.forEach((tab: NamedSection) => {
        tab.components.forEach((component: SectionContent) => {
            componentLookup[component.component] = defineAsyncComponent(
                () =>
                    import(
                        `@/arches_provenance/EditableReport/components/${component.component}.vue`
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
