import { localizeLabel } from "@/arches_modular_reports/ResourceReport/utils/localize-label.ts";

import type { WorkspaceConfig } from "@/arches_modular_reports/ResourceReport/types.ts";

export function folioLocations(
    workspaceConfigs: WorkspaceConfig[],
    activeLanguage: string,
): Record<string, string> {
    const locationsByNodegroupAlias: Record<string, string> = {};
    for (const workspaceConfig of workspaceConfigs) {
        for (const tab of workspaceConfig.config?.tabs ?? []) {
            for (const section of tab.sections ?? []) {
                const location = [
                    localizeLabel(tab.label, activeLanguage),
                    localizeLabel(section.label, activeLanguage),
                ]
                    .filter(Boolean)
                    .join(" / ");
                for (const folio of section.folios ?? []) {
                    locationsByNodegroupAlias[folio.nodegroup_alias] ??=
                        location;
                }
            }
        }
    }
    return locationsByNodegroupAlias;
}
