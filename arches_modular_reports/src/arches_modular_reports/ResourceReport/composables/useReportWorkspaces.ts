import { computed, ref, toValue } from "vue";

import { resolveWorkspaces } from "@/arches_modular_reports/ResourceReport/utils/resolve-workspaces.ts";

import type { ComputedRef, MaybeRefOrGetter } from "vue";
import type {
    ResolvedWorkspace,
    WorkspaceConfig,
} from "@/arches_modular_reports/ResourceReport/types.ts";

export interface ReportWorkspacesState {
    workspaces: ComputedRef<ResolvedWorkspace[]>;
    activeWorkspace: ComputedRef<ResolvedWorkspace | undefined>;
    selectWorkspace: (workspaceId: string) => void;
}

export function useReportWorkspaces(
    workspaceConfigs: MaybeRefOrGetter<WorkspaceConfig[]>,
    canEdit: MaybeRefOrGetter<boolean>,
    activeLanguage: MaybeRefOrGetter<string>,
): ReportWorkspacesState {
    const selectedWorkspaceId = ref<string | null>(null);

    const workspaces = computed(() =>
        resolveWorkspaces(toValue(workspaceConfigs), {
            canEdit: toValue(canEdit),
            activeLanguage: toValue(activeLanguage),
        }),
    );

    const activeWorkspace = computed(
        () =>
            workspaces.value.find(
                (workspace) => workspace.id === selectedWorkspaceId.value,
            ) ?? workspaces.value[0],
    );

    function selectWorkspace(workspaceId: string): void {
        selectedWorkspaceId.value = workspaceId;
    }

    return { workspaces, activeWorkspace, selectWorkspace };
}
