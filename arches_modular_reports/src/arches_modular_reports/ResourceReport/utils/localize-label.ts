import type { LocalizedLabel } from "@/arches_modular_reports/ResourceReport/types.ts";

export function localizeLabel(
    label: LocalizedLabel | undefined,
    activeLanguage: string,
): string | undefined {
    if (label === undefined) {
        return undefined;
    }
    if (typeof label === "string") {
        return label;
    }
    if (label[activeLanguage]) {
        return label[activeLanguage];
    }
    return Object.values(label).find((localizedText) => localizedText !== "");
}
