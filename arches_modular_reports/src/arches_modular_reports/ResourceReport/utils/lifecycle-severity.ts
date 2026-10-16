import type {
    LifecycleStateSummary,
    TagSeverity,
} from "@/arches_modular_reports/ResourceReport/types.ts";

export function lifecycleSeverity(
    lifecycleState: LifecycleStateSummary,
    configuredSeverities: Record<string, TagSeverity> = {},
): TagSeverity {
    if (lifecycleState.id in configuredSeverities) {
        return configuredSeverities[lifecycleState.id];
    }
    if (lifecycleState.is_initial_state) {
        return "info";
    }
    if (!lifecycleState.can_edit_resource_instances) {
        return "danger";
    }
    return "success";
}
