import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import OpenVue from "openvue/config";

import ViewStrip from "@/arches_modular_reports/ResourceReport/components/ViewStrip/ViewStrip.vue";

function mountViewStrip() {
    return mount(ViewStrip, {
        props: {
            activeViewId: "report",
            views: [
                {
                    id: "report",
                    label: "Report",
                    description: "",
                    component: "ReportView",
                    config: {},
                    layout: "report",
                },
                {
                    id: "graph",
                    label: "Graph",
                    description: "",
                    component: "GraphView",
                    config: {},
                    layout: "full",
                },
            ],
        },
        global: { plugins: [[OpenVue, { theme: "none" }]] },
    });
}

describe("ViewStrip", () => {
    it("renders a tab for each view", () => {
        const wrapper = mountViewStrip();

        expect(
            wrapper.findAll('[role="tab"]').map((tab) => tab.text()),
        ).toEqual(["Report", "Graph"]);
    });

    it("emits the selected view id", async () => {
        const wrapper = mountViewStrip();

        await wrapper.findAll('[role="tab"]')[1].trigger("click");

        expect(wrapper.emitted("select-view")).toEqual([["graph"]]);
    });
});
