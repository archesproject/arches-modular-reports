import numeral from "numeral";

import { defineAsyncComponent, isRef } from "vue";
import type { Component, Ref } from "vue";

import type {
    ComponentLookup,
    NamedSection,
    SectionContent,
    LanguageSettings,
    NumberFormat,
} from "@/arches_modular_reports/ModularReport/types";

export function uniqueId(_unused: unknown) {
    /* Not cryptographically secure, but good enough for Vue component keys. */
    return Math.floor(Math.random() * Date.now());
}

export function loadComponent(componentPath: string): Component {
    return defineAsyncComponent(() => import(`@/${componentPath}.vue`));
}

export async function importComponents(
    namedSections: NamedSection[],
    componentLookup: ComponentLookup,
): Promise<void> {
    namedSections.forEach((section: NamedSection) => {
        section.components.forEach((component: SectionContent) => {
            componentLookup[component.component] = {
                component: loadComponent(component.component),
                key: uniqueId(component),
            };
        });
    });
}

export function formatNumber(
    value: string | number,
    numberFormat: NumberFormat,
    languageSettings: LanguageSettings | Ref<LanguageSettings>,
) {
    const language = isRef(languageSettings)
        ? (languageSettings.value as LanguageSettings).ACTIVE_LANGUAGE
        : languageSettings.ACTIVE_LANGUAGE;
    const prefix = numberFormat.prefix?.[language] ?? "";
    const suffix = numberFormat.suffix?.[language] ?? "";
    return `${prefix}${numeral(value).format(numberFormat.format)}${suffix}`;
}
