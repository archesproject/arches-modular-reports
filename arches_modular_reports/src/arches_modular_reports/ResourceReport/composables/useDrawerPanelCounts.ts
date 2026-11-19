import { shallowRef, watch } from "vue";

import {
    fetchEditHistory,
    fetchRelatedResourceGroups,
    fetchResourceImages,
} from "@/arches_modular_reports/ResourceReport/api.ts";

import type { ComputedRef, ShallowRef } from "vue";
import type {
    ComponentNode,
    DrawerPanelCount,
    ImagesPanelConfig,
    LabelledConfig,
    RelatedResourcesPanelConfig,
    ReportData,
} from "@/arches_modular_reports/ResourceReport/types.ts";

type PanelCountLoader = (
    resourceInstanceId: string,
    config: LabelledConfig,
) => Promise<DrawerPanelCount>;

const PANEL_COUNT_LOADERS: Record<string, PanelCountLoader> = {
    EditHistoryPanel: countEditHistory,
    ImagesPanel: countImages,
    RelatedResourcesPanel: countRelatedResources,
};

export function useDrawerPanelCounts(
    panels: ComputedRef<ComponentNode<LabelledConfig>[]>,
    reportData: ComputedRef<ReportData>,
): ShallowRef<Map<ComponentNode<LabelledConfig>, DrawerPanelCount>> {
    const counts = shallowRef(
        new Map<ComponentNode<LabelledConfig>, DrawerPanelCount>(),
    );
    let latestCountsRequestNumber = 0;

    watch(
        [panels, () => reportData.value.resource.resourceinstanceid],
        () => {
            loadCounts();
        },
        { immediate: true },
    );

    watch(
        () => reportData.value.changeSet.isSaving.value,
        (isSaving, wasSaving) => {
            if (
                wasSaving &&
                !isSaving &&
                reportData.value.changeSet.saveError.value === null
            ) {
                loadCounts();
            }
        },
    );

    async function loadCounts(): Promise<void> {
        latestCountsRequestNumber += 1;
        const countsRequestNumber = latestCountsRequestNumber;
        const resourceInstanceId = reportData.value.resource.resourceinstanceid;
        const loadedCounts = await Promise.all(
            panels.value.map((panel) => countPanel(panel, resourceInstanceId)),
        );
        if (countsRequestNumber !== latestCountsRequestNumber) {
            return;
        }
        const nextCounts = new Map<
            ComponentNode<LabelledConfig>,
            DrawerPanelCount
        >();
        panels.value.forEach((panel, panelIndex) => {
            const panelCount = loadedCounts[panelIndex];
            if (panelCount !== null) {
                nextCounts.set(panel, panelCount);
            }
        });
        counts.value = nextCounts;
    }

    return counts;
}

async function countPanel(
    panel: ComponentNode<LabelledConfig>,
    resourceInstanceId: string,
): Promise<DrawerPanelCount | null> {
    const componentName = panel.component.split("/").at(-1) ?? "";
    const countLoader = PANEL_COUNT_LOADERS[componentName];
    if (countLoader === undefined) {
        return null;
    }
    try {
        return await countLoader(resourceInstanceId, panel.config);
    } catch {
        return null;
    }
}

async function countEditHistory(
    resourceInstanceId: string,
): Promise<DrawerPanelCount> {
    const historyPage = await fetchEditHistory(resourceInstanceId, null, "");
    return {
        count: historyPage.results.length,
        hasMore: historyPage.next_cursor !== null,
    };
}

async function countImages(
    resourceInstanceId: string,
    config: ImagesPanelConfig,
): Promise<DrawerPanelCount> {
    const imagesPage = await fetchResourceImages(
        resourceInstanceId,
        config.images ?? [],
        null,
    );
    return {
        count: imagesPage.images.length,
        hasMore: imagesPage.next_cursor !== null,
    };
}

async function countRelatedResources(
    resourceInstanceId: string,
    config: RelatedResourcesPanelConfig,
): Promise<DrawerPanelCount> {
    const groups = await fetchRelatedResourceGroups(
        resourceInstanceId,
        config.graphs ?? [],
        "",
    );
    return {
        count: groups.reduce((total, group) => total + group.items.length, 0),
        hasMore: groups.some((group) => group.next_cursor !== null),
    };
}
