import { describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";
import OpenVue from "openvue/config";

import ReportHeader from "@/arches_modular_reports/ResourceReport/components/ReportHeader/ReportHeader.vue";

import type { LifecycleStateSummary } from "@/arches_modular_reports/ResourceReport/types.ts";

vi.mock("@/arches_modular_reports/ResourceReport/api.ts", () => ({
    buildExportUrl: (resourceInstanceId: string, exportFormat: string) =>
        `/export/${exportFormat}/${resourceInstanceId}`,
}));

const DRAFT: LifecycleStateSummary = {
    id: "draft",
    name: "Draft",
    action_label: "Revert to Draft",
    is_initial_state: true,
    can_edit_resource_instances: true,
    can_delete_resource_instances: true,
};
const RETIRED: LifecycleStateSummary = {
    id: "retired",
    name: "Retired",
    action_label: "Retire",
    is_initial_state: false,
    can_edit_resource_instances: false,
    can_delete_resource_instances: false,
};

function mountHeader({
    previousStates = [],
    nextStates = [],
}: {
    previousStates?: LifecycleStateSummary[];
    nextStates?: LifecycleStateSummary[];
} = {}) {
    return mount(ReportHeader, {
        props: {
            displayName: "Cobalt blue",
            graphName: "Reference and Sample Collection Item",
            graphIconClass: "fa fa-asterisk",
            lifecycleStateName: "Active",
            lifecycleSeverity: "success",
            previousStates,
            nextStates,
            isTransitioning: false,
            summaryLines: [],
            exportFormats: ["json-ld", "csv"],
            resourceInstanceId: "resource-id",
        },
        global: { plugins: [[OpenVue, { theme: "none" }]] },
    });
}

describe("ReportHeader", () => {
    it("emits the target state of a lifecycle transition", async () => {
        const wrapper = mountHeader({
            previousStates: [DRAFT],
            nextStates: [RETIRED],
        });
        const transitionButtons = wrapper.findAll(
            ".report-header-lifecycle-actions button",
        );

        expect(transitionButtons.map((button) => button.text())).toEqual([
            "Revert to Draft",
            "Retire",
        ]);
        expect(transitionButtons[0].classes()).toContain("p-button-info");
        expect(transitionButtons[1].classes()).toContain("p-button-danger");

        await transitionButtons[1].trigger("click");

        expect(wrapper.emitted("transition-lifecycle")).toEqual([["retired"]]);
    });

    it("links each export format to its export url", () => {
        const exportLinks = mountHeader().findAll(".report-header-exports a");

        expect(exportLinks.map((link) => link.attributes("href"))).toEqual([
            "/export/json-ld/resource-id",
            "/export/csv/resource-id",
        ]);
        expect(exportLinks.map((link) => link.text())).toEqual([
            "JSON-LD",
            "CSV",
        ]);
    });
});
