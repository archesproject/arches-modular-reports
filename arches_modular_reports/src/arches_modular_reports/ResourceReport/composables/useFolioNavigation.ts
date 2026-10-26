import { nextTick, ref } from "vue";

import {
    indexGraphNodes,
    nodegroupLineage,
} from "@/arches_modular_reports/ResourceReport/utils/graph-nodes.ts";

import type { Ref } from "vue";
import type { NodegroupWidgetConfig } from "@/arches_vue_components/types.ts";
import type {
    FolioNavigation,
    FolioRevealer,
} from "@/arches_modular_reports/ResourceReport/types.ts";

const REVEAL_PASSES = 3;

export function useFolioNavigation(
    nodegroupWidgetConfigs: Ref<Record<string, NodegroupWidgetConfig> | null>,
): FolioNavigation {
    const folioElements = new Map<string, HTMLElement>();
    const revealers = new Set<FolioRevealer>();
    const flashedNodegroupAlias = ref<string | null>(null);

    function registerFolio(
        nodegroupAlias: string,
        element: HTMLElement,
    ): () => void {
        folioElements.set(nodegroupAlias, element);
        return () => {
            if (folioElements.get(nodegroupAlias) === element) {
                folioElements.delete(nodegroupAlias);
            }
        };
    }

    function registerRevealer(revealer: FolioRevealer): () => void {
        revealers.add(revealer);
        return () => {
            revealers.delete(revealer);
        };
    }

    function isReachable(nodegroupAlias: string): boolean {
        return (
            folioElements.has(nodegroupAlias) ||
            [...revealers].some((revealer) => revealer.contains(nodegroupAlias))
        );
    }

    async function revealFolio(nodegroupAlias: string): Promise<void> {
        for (
            let pass = 0;
            pass < REVEAL_PASSES && !folioElements.has(nodegroupAlias);
            pass += 1
        ) {
            for (const revealer of revealers) {
                revealer.reveal(nodegroupAlias);
            }
            await nextTick();
        }
    }

    async function jumpToNode(nodeAlias: string): Promise<void> {
        if (nodegroupWidgetConfigs.value === null) {
            return;
        }
        const graphNodesByAlias = indexGraphNodes(nodegroupWidgetConfigs.value);
        const targetNodegroupAlias = nodegroupLineage(
            nodegroupWidgetConfigs.value,
            graphNodesByAlias[nodeAlias].nodegroupAlias,
        ).find(isReachable);
        if (targetNodegroupAlias === undefined) {
            return;
        }

        flashedNodegroupAlias.value = null;
        await revealFolio(targetNodegroupAlias);

        folioElements
            .get(targetNodegroupAlias)
            ?.scrollIntoView({ block: "center" });
        flashedNodegroupAlias.value = targetNodegroupAlias;
    }

    function clearFlash(): void {
        flashedNodegroupAlias.value = null;
    }

    return {
        flashedNodegroupAlias,
        registerFolio,
        registerRevealer,
        jumpToNode,
        clearFlash,
    };
}
