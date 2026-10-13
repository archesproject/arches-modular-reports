import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";

import ReportView from "@/arches_modular_reports/ResourceReport/components/ReportView/ReportView.vue";

describe("ReportView", () => {
    it("renders its placeholder", () => {
        const wrapper = mount(ReportView);

        expect(wrapper.find("i").classes()).toEqual(
            "pi pi-th-large".split(" "),
        );
        expect(wrapper.text()).toBe("Report cards are not available yet.");
    });
});
