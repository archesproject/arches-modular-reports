import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";

import ReportPlaceholder from "@/arches_modular_reports/ResourceReport/components/ReportPlaceholder/ReportPlaceholder.vue";

describe("ReportPlaceholder", () => {
    it("renders the icon and the message", () => {
        const wrapper = mount(ReportPlaceholder, {
            props: { icon: "pi pi-sitemap", message: "Coming soon" },
        });

        expect(wrapper.find("i").classes()).toEqual(["pi", "pi-sitemap"]);
        expect(wrapper.find("i").attributes("aria-hidden")).toBe("true");
        expect(wrapper.text()).toBe("Coming soon");
    });
});
