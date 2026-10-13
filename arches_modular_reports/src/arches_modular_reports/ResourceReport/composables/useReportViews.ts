import { computed, ref, toValue } from "vue";

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
    viewConfigs: MaybeRefOrGetter<ViewConfig[]>,
    canEdit: MaybeRefOrGetter<boolean>,
    activeLanguage: MaybeRefOrGetter<string>,
): ReportViewsState {
    const selectedViewId = ref<string | null>(null);

    const views = computed(() =>
        resolveViews(toValue(viewConfigs), {
            canEdit: toValue(canEdit),
            activeLanguage: toValue(activeLanguage),
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
