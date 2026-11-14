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
            const containingRevealers = [...revealers].filter((revealer) =>
                revealer.contains(nodegroupAlias),
            );
            const localRevealers = containingRevealers.filter(
                (revealer) => revealer.isLocal === true,
            );
            const chosenRevealers =
                localRevealers.length > 0
                    ? localRevealers
                    : containingRevealers;
            for (const revealer of chosenRevealers) {
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
        await jumpToNodegroup(graphNodesByAlias[nodeAlias].nodegroupAlias);
    }

    // Lands on the nearest shown folio in the nodegroup's lineage. Focus
    // follows when the folio's element can take it (tabindex="-1").
    async function jumpToNodegroup(nodegroupAlias: string): Promise<void> {
        if (nodegroupWidgetConfigs.value === null) {
            return;
        }
        const targetNodegroupAlias = nodegroupLineage(
            nodegroupWidgetConfigs.value,
            nodegroupAlias,
        ).find(isReachable);
        if (targetNodegroupAlias === undefined) {
            return;
        }

        flashedNodegroupAlias.value = null;
        await revealFolio(targetNodegroupAlias);

        const folioElement = folioElements.get(targetNodegroupAlias);
        folioElement?.scrollIntoView({ block: "center" });
        if (folioElement?.hasAttribute("tabindex")) {
            folioElement.focus({ preventScroll: true });
        }
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
        jumpToNodegroup,
        clearFlash,
    };
}
