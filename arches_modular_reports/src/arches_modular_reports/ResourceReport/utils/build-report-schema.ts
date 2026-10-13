import { SEMANTIC_DATATYPE } from "@/arches_modular_reports/ResourceReport/constants.ts";

import type { NodePresentationLookup } from "@/arches_modular_reports/ModularReport/types.ts";
import type {
    ReportSchema,
    SchemaNode,
    SchemaNodegroup,
} from "@/arches_modular_reports/ResourceReport/types.ts";

export function buildReportSchema(
    nodePresentationLookup: NodePresentationLookup,
): ReportSchema {
    const nodesByAlias: Record<string, SchemaNode> = {};
    const nodegroupsByAlias: Record<string, SchemaNodegroup> = {};
    const nodegroupAliasesById: Record<string, string> = {};

    for (const [alias, nodePresentation] of Object.entries(
        nodePresentationLookup,
    )) {
        nodesByAlias[alias] = { ...nodePresentation, alias };

        const nodegroupAlias = nodePresentation.nodegroup.alias;
        if (nodegroupAlias === null || nodegroupAlias in nodegroupsByAlias) {
            continue;
        }
        nodegroupsByAlias[nodegroupAlias] = {
            alias: nodegroupAlias,
            nodegroupId: nodePresentation.nodegroup.nodegroup_id,
            parentNodegroupId: nodePresentation.nodegroup.parent_nodegroup_id,
            cardinality: nodePresentation.nodegroup.cardinality,
            cardName: nodePresentation.card_name,
            cardOrder: nodePresentation.card_order,
            cardVisible: nodePresentation.card_visible,
            writable: nodePresentation.nodegroup.writable,
            nodes: [],
            childAliases: [],
        };
        nodegroupAliasesById[nodePresentation.nodegroup.nodegroup_id] =
            nodegroupAlias;
    }

    for (const schemaNode of Object.values(nodesByAlias)) {
        const nodegroupAlias = schemaNode.nodegroup.alias;
        if (
            nodegroupAlias === null ||
            schemaNode.datatype === SEMANTIC_DATATYPE ||
            !schemaNode.visible
        ) {
            continue;
        }
        nodegroupsByAlias[nodegroupAlias].nodes.push(schemaNode);
    }

    const topLevelNodegroups: SchemaNodegroup[] = [];
    for (const schemaNodegroup of Object.values(nodegroupsByAlias)) {
        schemaNodegroup.nodes.sort(
            (firstNode, secondNode) =>
                firstNode.widget_order - secondNode.widget_order,
        );
        if (!schemaNodegroup.cardVisible) {
            continue;
        }
        if (schemaNodegroup.parentNodegroupId === null) {
            topLevelNodegroups.push(schemaNodegroup);
            continue;
        }
        const parentAlias =
            nodegroupAliasesById[schemaNodegroup.parentNodegroupId];
        if (parentAlias !== undefined) {
            nodegroupsByAlias[parentAlias].childAliases.push(
                schemaNodegroup.alias,
            );
        }
    }

    for (const schemaNodegroup of Object.values(nodegroupsByAlias)) {
        schemaNodegroup.childAliases.sort(
            (firstAlias, secondAlias) =>
                nodegroupsByAlias[firstAlias].cardOrder -
                nodegroupsByAlias[secondAlias].cardOrder,
        );
    }

    return {
        nodesByAlias,
        nodegroupsByAlias,
        topLevelNodegroupAliases: topLevelNodegroups
            .sort(
                (firstNodegroup, secondNodegroup) =>
                    firstNodegroup.cardOrder - secondNodegroup.cardOrder,
            )
            .map((schemaNodegroup) => schemaNodegroup.alias),
    };
}
