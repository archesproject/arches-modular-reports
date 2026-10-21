import type { LocalizedLabel } from "@/arches_modular_reports/ResourceReport/types.ts";

export function localizeLabel(
    label: LocalizedLabel | null,
    activeLanguage: string,
): string {
    if (label === null) {
        return "";
    }
    if (typeof label === "string") {
        return label;
    }
    if (label[activeLanguage]) {
        return label[activeLanguage];
    }
    return (
        Object.values(label).find((localizedText) => localizedText !== "") ?? ""
    );
}
