import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";

import DataView from "@/arches_modular_reports/ResourceReport/components/DataView/DataView.vue";

describe("DataView", () => {
    it("renders its placeholder", () => {
        const wrapper = mount(DataView);

        expect(wrapper.find("i").classes()).toEqual(
            "pi pi-database".split(" "),
        );
        expect(wrapper.text()).toBe("The data browser is not available yet.");
    });
});
