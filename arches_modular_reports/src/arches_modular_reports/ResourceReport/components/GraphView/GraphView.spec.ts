import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";

import GraphView from "@/arches_modular_reports/ResourceReport/components/GraphView/GraphView.vue";

describe("GraphView", () => {
    it("renders its placeholder", () => {
        const wrapper = mount(GraphView);

        expect(wrapper.find("i").classes()).toEqual("pi pi-sitemap".split(" "));
        expect(wrapper.text()).toBe(
            "A graph view of this resource is coming soon.",
        );
    });
});
