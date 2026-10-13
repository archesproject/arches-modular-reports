import {
    DATA_VIEW,
    REPORT_VIEW,
} from "@/arches_modular_reports/ResourceReport/constants.ts";
import { localizeLabel } from "@/arches_modular_reports/ResourceReport/utils/localize-label.ts";

import type {
    ResolvedView,
    ViewConfig,
    ViewLayout,
} from "@/arches_modular_reports/ResourceReport/types.ts";

function viewLayout(component: string): ViewLayout {
    if (component === REPORT_VIEW) {
        return "report";
    }
    if (component === DATA_VIEW) {
        return "data";
    }
    return "full";
}

export function resolveViews(
    viewConfigs: ViewConfig[],
    { canEdit, activeLanguage }: { canEdit: boolean; activeLanguage: string },
): ResolvedView[] {
    return viewConfigs
        .filter((viewConfig) => canEdit || viewConfig.component !== DATA_VIEW)
        .map((viewConfig) => ({
            id: viewConfig.id,
            label:
                localizeLabel(viewConfig.label, activeLanguage) ??
                viewConfig.id,
            description:
                localizeLabel(viewConfig.description, activeLanguage) ?? "",
            component: viewConfig.component,
            config: viewConfig.config ?? {},
            layout: viewLayout(viewConfig.component),
        }));
}
