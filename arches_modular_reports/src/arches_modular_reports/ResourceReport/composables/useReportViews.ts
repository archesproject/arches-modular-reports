import { computed, ref, toValue } from "vue";
import { useGettext } from "vue3-gettext";

import {
    DATA_VIEW,
    GRAPH_VIEW,
    REPORT_VIEW,
} from "@/arches_modular_reports/ResourceReport/constants.ts";
import { resolveViews } from "@/arches_modular_reports/ResourceReport/utils/resolve-views.ts";

import type { ComputedRef, MaybeRefOrGetter } from "vue";
import type {
    ResolvedView,
    ViewConfig,
} from "@/arches_modular_reports/ResourceReport/types.ts";

export interface ReportViewsState {
    views: ComputedRef<ResolvedView[]>;
    activeView: ComputedRef<ResolvedView | undefined>;
    selectView: (viewId: string) => void;
}

export function useReportViews(
    viewConfigs: MaybeRefOrGetter<ViewConfig[] | undefined>,
    canEdit: MaybeRefOrGetter<boolean>,
    activeLanguage: MaybeRefOrGetter<string>,
): ReportViewsState {
    const { $gettext } = useGettext();

    const builtInViewText = {
        [REPORT_VIEW]: {
            label: $gettext("Report"),
            description: $gettext("A curated summary of this resource's data"),
        },
        [DATA_VIEW]: {
            label: $gettext("Data"),
            description: $gettext(
                "Browse and edit every field recorded on this resource",
            ),
        },
        [GRAPH_VIEW]: {
            label: $gettext("Graph"),
            description: $gettext(
                "A visual overview of how this resource connects to its data",
            ),
        },
    };

    const selectedViewId = ref<string | null>(null);

    const views = computed(() =>
        resolveViews(toValue(viewConfigs), {
            canEdit: toValue(canEdit),
            activeLanguage: toValue(activeLanguage),
            builtInViewText,
        }),
    );

    const activeView = computed(
        () =>
            views.value.find((view) => view.id === selectedViewId.value) ??
            views.value[0],
    );

    function selectView(viewId: string): void {
        selectedViewId.value = viewId;
    }

    return { views, activeView, selectView };
}
