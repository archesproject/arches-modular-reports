import { describe, expect, it } from "vitest";

import { lifecycleSeverity } from "@/arches_modular_reports/ResourceReport/utils/lifecycle-severity.ts";

const DRAFT = {
    id: "draft",
    name: "Draft",
    action_label: "Revert to Draft",
    is_initial_state: true,
    can_edit_resource_instances: true,
    can_delete_resource_instances: true,
};
const ACTIVE = {
    ...DRAFT,
    id: "active",
    name: "Active",
    is_initial_state: false,
    can_delete_resource_instances: false,
};
const RETIRED = {
    ...ACTIVE,
    id: "retired",
    can_edit_resource_instances: false,
};

describe("lifecycleSeverity", () => {
    it("derives severity from the state's flags", () => {
        expect(lifecycleSeverity(DRAFT)).toBe("info");
        expect(lifecycleSeverity(ACTIVE)).toBe("success");
        expect(lifecycleSeverity(RETIRED)).toBe("danger");
    });

    it("lets config override the derived severity", () => {
        expect(lifecycleSeverity(ACTIVE, { active: "warn" })).toBe("warn");
    });
});
