import { defineComponent, h } from "vue";
import type { PropType } from "vue";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import OpenVue from "openvue/config";

import ModularReport from "@/arches_modular_reports/ModularReport/ModularReport.vue";

import { fetchReportConfig } from "@/arches_modular_reports/ModularReport/api.ts";
import { importComponents } from "@/arches_modular_reports/ModularReport/utils.ts";

import type {
    ComponentLookup,
    NamedSection,
    SectionContent,
} from "@/arches_modular_reports/ModularReport/types.ts";

vi.mock("@/arches_modular_reports/ModularReport/api.ts", () => ({
    fetchReportConfig: vi.fn(),
}));

vi.mock("@/arches_modular_reports/ModularReport/utils.ts", () => ({
    importComponents: vi.fn(),
}));

const StubSection = defineComponent({
    props: {
        component: { type: Object as PropType<SectionContent>, required: true },
        resourceInstanceId: { type: String, required: true },
    },
    setup(props) {
        return () =>
            h(
                "div",
                { class: "stub-section" },
                `${props.component.component}:${props.resourceInstanceId}`,
            );
    },
});

function mountModularReport(resourceInstanceId?: string) {
    return mount(ModularReport, {
        props: { graphSlug: "graph-slug", resourceInstanceId },
        global: { plugins: [[OpenVue, { theme: "none" }]] },
    });
}

describe("ModularReport", () => {
    beforeEach(() => {
        vi.clearAllMocks();
        vi.mocked(importComponents).mockImplementation(
            async (
                namedSections: NamedSection[],
                componentLookup: ComponentLookup,
            ) => {
                for (const namedSection of namedSections) {
                    for (const sectionContent of namedSection.components) {
                        componentLookup[sectionContent.component] = {
                            component: StubSection,
                            key: 0,
                        };
                    }
                }
            },
        );
    });

    it("asks for a resource when none is given", async () => {
        const wrapper = mountModularReport();
        await flushPromises();

        expect(wrapper.text()).toBe("Open a resource to see its report.");
        expect(fetchReportConfig).not.toHaveBeenCalled();
    });

    it("renders each configured component in order", async () => {
        vi.mocked(fetchReportConfig).mockResolvedValue({
            name: "Default",
            components: [
                { component: "app/First", config: {} },
                { component: "app/Second", config: {} },
            ],
        });
        const wrapper = mountModularReport("resource-id");
        await flushPromises();

        expect(
            wrapper.findAll(".stub-section").map((section) => section.text()),
        ).toEqual(["app/First:resource-id", "app/Second:resource-id"]);
    });

    it("reports a config that cannot be loaded", async () => {
        vi.mocked(fetchReportConfig).mockRejectedValue(new Error("Not found"));
        const wrapper = mountModularReport("resource-id");
        await flushPromises();

        expect(wrapper.text()).toContain(
            "Unable to load the report: %{message}",
        );
    });
});
