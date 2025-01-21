import { defineAsyncComponent } from "vue";

import type {
    ComponentLookup,
    NamedSection,
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
