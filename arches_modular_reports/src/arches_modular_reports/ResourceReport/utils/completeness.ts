import {
    childNodegroupAliases,
    nodegroupLineage,
} from "@/arches_modular_reports/ResourceReport/utils/graph-nodes.ts";
import {
    nodegroupTiles,
    tileHasData,
} from "@/arches_modular_reports/ResourceReport/utils/tiles.ts";

import type {
    AliasedData,
    NodegroupWidgetConfig,
} from "@/arches_vue_components/types.ts";
import type { ReportTabGroup } from "@/arches_modular_reports/ResourceReport/types.ts";

export interface CompletenessCard {
    nodegroupAlias: string;
    name: string;
    hasData: boolean;
    isRequired: boolean;
}

export interface CompletenessGroup {
    tabLabel: string | null;
    cards: CompletenessCard[];
}

export function completenessCards(
    nodegroupWidgetConfigs: Record<string, NodegroupWidgetConfig>,
    aliasedData: AliasedData,
    isPendingDelete: (tileId: string) => boolean,
): CompletenessCard[] {
    return childNodegroupAliases(nodegroupWidgetConfigs, null).map(
        (nodegroupAlias) => {
            const nodegroupWidgetConfig =
                nodegroupWidgetConfigs[nodegroupAlias];
            return {
                nodegroupAlias,
                name: nodegroupWidgetConfig.card?.name ?? nodegroupAlias,
                hasData: nodegroupTiles(aliasedData[nodegroupAlias]).some(
                    (tile) =>
                        tileHasData(tile) &&
                        !isPendingDelete(tile.tileid ?? ""),
                ),
                isRequired: nodegroupWidgetConfig.card_x_node_x_widgets.some(
                    (widget) => widget.node.isrequired,
                ),
            };
        },
    );
}

export function groupCardsByReportTab(
    cards: CompletenessCard[],
    reportTabs: ReportTabGroup[],
    nodegroupWidgetConfigs: Record<string, NodegroupWidgetConfig>,
): CompletenessGroup[] {
    const cardsByAlias = new Map(
        cards.map((card) => [card.nodegroupAlias, card]),
    );
    const placedAliases = new Set<string>();

    const tabGroups = reportTabs.map((reportTab) => {
        const tabCards: CompletenessCard[] = [];
        for (const nodegroupAlias of reportTab.nodegroupAliases) {
            const topLevelAlias = nodegroupLineage(
                nodegroupWidgetConfigs,
                nodegroupAlias,
            ).at(-1);
            if (topLevelAlias === undefined) {
                continue;
            }
            const card = cardsByAlias.get(topLevelAlias);
            if (card !== undefined && !placedAliases.has(card.nodegroupAlias)) {
                placedAliases.add(card.nodegroupAlias);
                tabCards.push(card);
            }
        }
        return { tabLabel: reportTab.label, cards: tabCards };
    });

    const unplacedCards = cards.filter(
        (card) => !placedAliases.has(card.nodegroupAlias),
    );
    return [...tabGroups, { tabLabel: null, cards: unplacedCards }].filter(
        (group) => group.cards.length > 0,
    );
}
