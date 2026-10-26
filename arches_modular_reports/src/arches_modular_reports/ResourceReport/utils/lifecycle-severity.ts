import type {
    LifecycleStateSummary,
    TagSeverity,
} from "@/arches_modular_reports/ResourceReport/types.ts";

export function lifecycleSeverity(
    lifecycleState: LifecycleStateSummary,
): TagSeverity {
    if (lifecycleState.is_initial_state) {
        return "info";
    }
    if (!lifecycleState.can_edit_resource_instances) {
        return "danger";
    }
    return "success";
}
