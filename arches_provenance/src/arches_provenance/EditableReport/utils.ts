import { defineAsyncComponent } from "vue";

import type {
    ComponentLookup,
    NamedSection,
    NodeValueDisplayData,
    SectionContent,
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
            componentLookup[component.component] = {
                component: defineAsyncComponent(() =>
                    import(
                        `@/arches_provenance/EditableReport/components/${component.component}.vue`
                    ).catch(
                        () =>
                            import(
                                `@/arches_provenance/EditableReport/components/${component.component}/${component.component}.vue`
                            ),
                    ),
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
