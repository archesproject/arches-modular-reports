import { plainText } from "@/arches_modular_reports/ResourceReport/utils/plain-text.ts";

import type { AliasedNodeData } from "@/arches_vue_components/types.ts";
import type { LanguageValue } from "@/arches_vue_components/datatypes/string/types.ts";

export interface LocalizedText {
    languageCode: string;
    value: string;
    direction: LanguageValue["direction"];
}

function isLanguageValue(value: unknown): value is LanguageValue {
    return (
        typeof value === "object" &&
        value !== null &&
        typeof (value as { value?: unknown }).value === "string"
    );
}

function isLocalizedNodeValue(
    nodeValue: unknown,
): nodeValue is Record<string, LanguageValue> {
    if (
        typeof nodeValue !== "object" ||
        nodeValue === null ||
        Array.isArray(nodeValue)
    ) {
        return false;
    }
    const languageValues = Object.values(nodeValue);
    return languageValues.length > 0 && languageValues.every(isLanguageValue);
}

export function localizedTexts(
    nodeData: AliasedNodeData | null,
    activeLanguage: string,
): LocalizedText[] {
    if (nodeData === null || !isLocalizedNodeValue(nodeData.node_value)) {
        return [];
    }
    return Object.entries(nodeData.node_value)
        .filter(
            ([, languageValue]) => plainText(languageValue.value).trim() !== "",
        )
        .map(([languageCode, languageValue]) => ({
            languageCode,
            value: languageValue.value,
            direction: languageValue.direction,
        }))
        .sort(
            (firstText, secondText) =>
                Number(secondText.languageCode === activeLanguage) -
                Number(firstText.languageCode === activeLanguage),
        );
}

export function hasOtherLanguages(
    texts: LocalizedText[],
    activeLanguage: string,
): boolean {
    return texts.some((text) => text.languageCode !== activeLanguage);
}

export function nodeText(nodeData: AliasedNodeData | null): string {
    if (nodeData === null) {
        return "";
    }
    const displayText = plainText(nodeData.display_value);
    if (displayText.trim() !== "") {
        return displayText;
    }
    const [firstText] = localizedTexts(nodeData, "");
    return firstText ? plainText(firstText.value) : "";
}

export function nodeHasData(nodeData: AliasedNodeData | null): boolean {
    return nodeText(nodeData).trim() !== "";
}

export function nodeSearchTexts(nodeData: AliasedNodeData): string[] {
    const texts = localizedTexts(nodeData, "");
    if (texts.length === 0) {
        return [plainText(nodeData.display_value)];
    }
    return texts.map((text) => plainText(text.value));
}
