import { escapeRegExp } from "es-toolkit";

import type { HighlightSegment } from "@/arches_modular_reports/ResourceReport/types.ts";

export function highlightSegments(
    text: string,
    query: string,
): HighlightSegment[] {
    if (query === "") {
        return [{ text, matched: false }];
    }
    const matchPattern = new RegExp(`(${escapeRegExp(query)})`, "gi");
    return text
        .split(matchPattern)
        .map((segment, segmentIndex) => ({
            text: segment,
            matched: segmentIndex % 2 === 1,
        }))
        .filter((segment) => segment.text !== "");
}
