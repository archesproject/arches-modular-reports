import { findNodeValues } from "@/arches_modular_reports/ResourceReport/utils/find-node-values.ts";
import { localizeLabel } from "@/arches_modular_reports/ResourceReport/utils/localize-label.ts";
import { nodeText } from "@/arches_modular_reports/ResourceReport/utils/localized-text.ts";

import type { AliasedData } from "@/arches_vue_components/types.ts";
import type {
    SummaryEntryConfig,
    SummaryRow,
} from "@/arches_modular_reports/ResourceReport/types.ts";

export function summaryRows(
    summaryEntries: SummaryEntryConfig[],
    aliasedData: AliasedData,
    activeLanguage: string,
    defaultLanguage: string,
): SummaryRow[] {
    return summaryEntries.map((summaryEntry) => ({
        nodeAlias: summaryEntry.node_alias,
        label: localizeLabel(
            summaryEntry.label,
            activeLanguage,
            defaultLanguage,
        ),
        values: findNodeValues(aliasedData, summaryEntry.node_alias)
            .map(nodeText)
            .filter((valueText) => valueText.trim() !== ""),
    }));
}
