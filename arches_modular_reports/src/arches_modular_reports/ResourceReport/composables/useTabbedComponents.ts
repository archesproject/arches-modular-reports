import { computed, onMounted, onUnmounted, ref } from "vue";

import { useReportData } from "@/arches_modular_reports/ResourceReport/composables/useReportData.ts";
import { nodegroupAliasesWithin } from "@/arches_modular_reports/ResourceReport/utils/component-tree.ts";
import { localizeLabel } from "@/arches_modular_reports/ResourceReport/utils/localize-label.ts";

import type { ComputedRef, Ref } from "vue";
import type {
    ComponentNode,
    LabelledConfig,
} from "@/arches_modular_reports/ResourceReport/types.ts";

export interface ComponentTab {
    node: ComponentNode<LabelledConfig>;
    label: string;
    description: string;
    nodegroupAliases: Set<string>;
}

export interface TabbedComponents {
    tabs: ComputedRef<ComponentTab[]>;
    activeTabIndex: Ref<number>;
    activeTab: ComputedRef<ComponentTab | undefined>;
}

export function useTabbedComponents(
    childNodes: () => ComponentNode<LabelledConfig>[],
): TabbedComponents {
    const reportData = useReportData();

    const activeTabIndex = ref(0);

    const tabs = computed(() =>
        childNodes()
            .filter(
                (childNode) =>
                    childNode.config.requires_edit !== true ||
                    reportData.value.canEdit,
            )
            .map((childNode) => ({
                node: childNode,
                label: localizeLabel(
                    childNode.config.label ?? null,
                    reportData.value.context.language,
                ),
                description: localizeLabel(
                    childNode.config.description ?? null,
                    reportData.value.context.language,
                ),
                nodegroupAliases: nodegroupAliasesWithin(childNode),
            })),
    );

    const activeTab = computed(
        () => tabs.value[activeTabIndex.value] ?? tabs.value[0],
    );

    let unregisterRevealer = (): void => undefined;

    onMounted(() => {
        unregisterRevealer = reportData.value.folioNavigation.registerRevealer({
            contains: (nodegroupAlias) =>
                tabs.value.some((tab) =>
                    tab.nodegroupAliases.has(nodegroupAlias),
                ),
            reveal: (nodegroupAlias) => {
                const tabIndex = tabs.value.findIndex((tab) =>
                    tab.nodegroupAliases.has(nodegroupAlias),
                );
                if (tabIndex !== -1) {
                    activeTabIndex.value = tabIndex;
                }
            },
        });
    });

    onUnmounted(() => {
        unregisterRevealer();
    });

    return { tabs, activeTabIndex, activeTab };
}
