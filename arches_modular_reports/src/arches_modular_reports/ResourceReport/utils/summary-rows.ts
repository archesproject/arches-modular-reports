import { findNodeValues } from "@/arches_modular_reports/ResourceReport/utils/find-node-values.ts";
import { localizeLabel } from "@/arches_modular_reports/ResourceReport/utils/localize-label.ts";
import { nodeText } from "@/arches_modular_reports/ResourceReport/utils/localized-text.ts";

import type { AliasedData } from "@/arches_vue_components/types.ts";
import type {
    NodeTextContext,
    SummaryEntryConfig,
    SummaryRow,
} from "@/arches_modular_reports/ResourceReport/types.ts";

export function summaryRows(
    summaryEntries: SummaryEntryConfig[],
    aliasedData: AliasedData,
    context: NodeTextContext,
): SummaryRow[] {
    return summaryEntries.map((summaryEntry) => ({
        nodeAlias: summaryEntry.node_alias,
        label: localizeLabel(
            summaryEntry.label,
            context.activeLanguage,
            context.defaultLanguage,
        ),
        values: findNodeValues(aliasedData, summaryEntry.node_alias)
            .map((nodeData) =>
                nodeText(summaryEntry.node_alias, nodeData, context),
            )
            .filter((valueText) => valueText.trim() !== ""),
    }));
}
