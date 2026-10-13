import {
    DATA_VIEW,
    DEFAULT_VIEW_CONFIGS,
    REPORT_VIEW,
} from "@/arches_modular_reports/ResourceReport/constants.ts";
import { localizeLabel } from "@/arches_modular_reports/ResourceReport/utils/localize-label.ts";

import type {
    ResolvedView,
    ViewConfig,
    ViewLayout,
} from "@/arches_modular_reports/ResourceReport/types.ts";

export interface BuiltInViewText {
    label: string;
    description: string;
}

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
    viewConfigs: ViewConfig[] | undefined,
    {
        canEdit,
        activeLanguage,
        builtInViewText,
    }: {
        canEdit: boolean;
        activeLanguage: string;
        builtInViewText: Record<string, BuiltInViewText>;
    },
): ResolvedView[] {
    return (viewConfigs ?? DEFAULT_VIEW_CONFIGS)
        .filter((viewConfig) => canEdit || viewConfig.component !== DATA_VIEW)
        .map((viewConfig) => {
            const defaultText = builtInViewText[viewConfig.component];
            return {
                id: viewConfig.id,
                label:
                    localizeLabel(viewConfig.label, activeLanguage) ??
                    defaultText?.label ??
                    viewConfig.id,
                description:
                    localizeLabel(viewConfig.description, activeLanguage) ??
                    defaultText?.description ??
                    "",
                component: viewConfig.component,
                config: viewConfig.config ?? {},
                layout: viewLayout(viewConfig.component),
            };
        });
}
