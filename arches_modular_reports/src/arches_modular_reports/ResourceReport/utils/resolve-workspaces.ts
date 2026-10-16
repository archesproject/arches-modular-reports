import { DATA_WORKSPACE } from "@/arches_modular_reports/ResourceReport/constants.ts";
import { localizeLabel } from "@/arches_modular_reports/ResourceReport/utils/localize-label.ts";

import type {
    ResolvedWorkspace,
    WorkspaceConfig,
} from "@/arches_modular_reports/ResourceReport/types.ts";

export function resolveWorkspaces(
    workspaceConfigs: WorkspaceConfig[],
    { canEdit, activeLanguage }: { canEdit: boolean; activeLanguage: string },
): ResolvedWorkspace[] {
    return workspaceConfigs
        .filter(
            (workspaceConfig) =>
                canEdit || workspaceConfig.component !== DATA_WORKSPACE,
        )
        .map((workspaceConfig) => ({
            id: workspaceConfig.id,
            label:
                localizeLabel(workspaceConfig.label, activeLanguage) ??
                workspaceConfig.id,
            description:
                localizeLabel(workspaceConfig.description, activeLanguage) ??
                "",
            component: workspaceConfig.component,
            config: workspaceConfig.config ?? {},
        }));
}
