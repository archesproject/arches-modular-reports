import { richTextToPlainText } from "@/arches_vue_components/widgets/RichTextWidget/utils.ts";

import type { AliasedNodeData } from "@/arches_vue_components/types.ts";
import type { LanguageValue } from "@/arches_vue_components/datatypes/string/types.ts";
import type { NodeTextContext } from "@/arches_modular_reports/ResourceReport/types.ts";

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

export function readableText(
    nodeAlias: string,
    text: string,
    context: NodeTextContext,
): string {
    if (context.richTextNodeAliases.has(nodeAlias)) {
        return richTextToPlainText(text);
    }
    return text;
}

function languageRank(languageCode: string, context: NodeTextContext): number {
    if (languageCode === context.activeLanguage) {
        return 0;
    }
    if (languageCode === context.defaultLanguage) {
        return 1;
    }
    return 2;
}

export function localizedTexts(
    nodeAlias: string,
    nodeData: AliasedNodeData | null,
    context: NodeTextContext,
): LocalizedText[] {
    if (nodeData === null || !isLocalizedNodeValue(nodeData.node_value)) {
        return [];
    }
    return Object.entries(nodeData.node_value)
        .filter(
            ([, languageValue]) =>
                readableText(nodeAlias, languageValue.value, context).trim() !==
                "",
        )
        .map(([languageCode, languageValue]) => ({
            languageCode,
            value: languageValue.value,
            direction: languageValue.direction,
        }))
        .sort(
            (firstText, secondText) =>
                languageRank(firstText.languageCode, context) -
                languageRank(secondText.languageCode, context),
        );
}

export function hasOtherLanguages(
    texts: LocalizedText[],
    activeLanguage: string,
): boolean {
    return texts.some((text) => text.languageCode !== activeLanguage);
}

export function nodeText(
    nodeAlias: string,
    nodeData: AliasedNodeData | null,
    context: NodeTextContext,
): string {
    if (nodeData === null) {
        return "";
    }
    const [firstText] = localizedTexts(nodeAlias, nodeData, context);
    if (firstText) {
        return readableText(nodeAlias, firstText.value, context);
    }
    return readableText(nodeAlias, nodeData.display_value, context);
}

export function nodeHasData(
    nodeAlias: string,
    nodeData: AliasedNodeData | null,
    context: NodeTextContext,
): boolean {
    return nodeText(nodeAlias, nodeData, context).trim() !== "";
}

export function nodeSearchTexts(
    nodeAlias: string,
    nodeData: AliasedNodeData,
    context: NodeTextContext,
): string[] {
    const texts = localizedTexts(nodeAlias, nodeData, context);
    if (texts.length === 0) {
        return [readableText(nodeAlias, nodeData.display_value, context)];
    }
    return texts.map((text) => readableText(nodeAlias, text.value, context));
}
