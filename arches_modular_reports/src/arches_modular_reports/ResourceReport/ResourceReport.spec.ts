import { beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import OpenVue from "openvue/config";

import ResourceReport from "@/arches_modular_reports/ResourceReport/ResourceReport.vue";

import {
    fetchModularReportResource,
    fetchNodePresentation,
} from "@/arches_modular_reports/ModularReport/api.ts";
import {
    fetchReportContext,
    updateLifecycleState,
} from "@/arches_modular_reports/ResourceReport/api.ts";

import type { NodePresentation } from "@/arches_modular_reports/ModularReport/types.ts";
import type {
    LifecycleStateSummary,
    ReportContext,
    ReportPermissions,
    ResourceReportConfig,
} from "@/arches_modular_reports/ResourceReport/types.ts";

vi.mock("@/arches_modular_reports/ModularReport/api.ts", () => ({
    fetchModularReportResource: vi.fn(),
    fetchNodePresentation: vi.fn(),
}));

vi.mock("@/arches_modular_reports/ResourceReport/api.ts", () => ({
    fetchReportContext: vi.fn(),
    updateLifecycleState: vi.fn(),
    buildExportUrl: () => "/export",
}));

const DRAFT: LifecycleStateSummary = {
    id: "draft",
    name: "Draft",
    action_label: "Revert to Draft",
    is_initial_state: true,
    can_edit_resource_instances: true,
    can_delete_resource_instances: true,
};
const ACTIVE: LifecycleStateSummary = {
    id: "active",
    name: "Active",
    action_label: "Make Active",
    is_initial_state: false,
    can_edit_resource_instances: true,
    can_delete_resource_instances: false,
};

function makeContext(
    permissions: Partial<ReportPermissions> = {},
): ReportContext {
    return {
        graph: {
            name: "Reference and Sample Collection Item",
            slug: "reference_and_sample_collection_item",
            iconclass: "fa fa-asterisk",
            color: null,
        },
        lifecycle_state: {
            ...DRAFT,
            next_resource_instance_lifecycle_states: [ACTIVE],
            previous_resource_instance_lifecycle_states: [],
        },
        language: "en",
        language_dir: "ltr",
        permissions: {
            can_edit: true,
            can_delete: true,
            can_copy: true,
            is_reviewer: true,
            is_rdm_admin: false,
            ...permissions,
        },
    };
}

function makeNodePresentation(
    datatype: string,
    widgetLabel: string,
): NodePresentation {
    return {
        nodeid: `${widgetLabel}-node`,
        name: widgetLabel,
        datatype,
        card_name: "Names",
        card_order: 0,
        card_visible: true,
        widget_label: widgetLabel,
        widget_order: 0,
        visible: true,
        nodegroup: {
            nodegroup_id: "names-nodegroup",
            cardinality: "n",
            alias: "names",
            parent_nodegroup_id: null,
            writable: true,
        },
        is_rich_text: false,
        is_numeric: false,
        is_required: false,
        number_format: { format: "", prefix: {}, suffix: {} },
    };
}

const NODE_PRESENTATION = {
    names: makeNodePresentation("semantic", "Names"),
    name_content: makeNodePresentation("string", "Name"),
};

const RESOURCE = {
    name: "Cobalt blue",
    graph_publication: "publication",
    principaluser: 1,
    aliased_data: {
        names: [
            {
                aliased_data: {
                    name_content: {
                        display_value: "Cobalt blue",
                        node_value: "Cobalt blue",
                        details: [],
                    },
                },
                nodegroup: "names-nodegroup",
                parenttile: null,
                provisionaledits: null,
                resourceinstance: "resource-id",
                sortorder: 0,
                tileid: "tile-id",
            },
        ],
    },
};

const REPORT_CONFIG: ResourceReportConfig = {
    header: { export_formats: ["json-ld"] },
    views: [
        {
            id: "report",
            component: "ReportView",
            label: { en: "Report" },
            description: { en: "A curated summary of this resource's data" },
            config: { tabs: [], home: { summary: [], drawer: [] } },
        },
        { id: "data", component: "DataView", label: { en: "Data" } },
        { id: "graph", component: "GraphView", label: { en: "Graph" } },
    ],
};

function mountReport(config: ResourceReportConfig = REPORT_CONFIG) {
    return mount(ResourceReport, {
        props: {
            component: {
                component:
                    "arches_modular_reports/ResourceReport/ResourceReport",
                config,
            },
            resourceInstanceId: "resource-id",
        },
        global: {
            plugins: [[OpenVue, { theme: "none" }]],
            provide: { graphSlug: "reference_and_sample_collection_item" },
        },
    });
}

function tabLabels(wrapper: ReturnType<typeof mountReport>): string[] {
    return wrapper.findAll('[role="tab"]').map((tab) => tab.text());
}

describe("ResourceReport", () => {
    beforeEach(() => {
        vi.clearAllMocks();
        vi.mocked(fetchReportContext).mockResolvedValue(makeContext());
        vi.mocked(fetchNodePresentation).mockResolvedValue(NODE_PRESENTATION);
        vi.mocked(fetchModularReportResource).mockResolvedValue(RESOURCE);
        vi.mocked(updateLifecycleState).mockResolvedValue();
    });

    it("shows a loading state until the report data arrives", () => {
        const wrapper = mountReport();

        expect(wrapper.find(".resource-report-loading").exists()).toBe(true);
    });

    it("renders the header and every view for editors", async () => {
        const wrapper = mountReport();
        await flushPromises();

        expect(wrapper.find("h2").text()).toBe("Cobalt blue");
        expect(tabLabels(wrapper)).toEqual(["Report", "Data", "Graph"]);
        expect(wrapper.find(".resource-report-caption").text()).toBe(
            "A curated summary of this resource's data",
        );
        expect(wrapper.find(".resource-report-splitter").exists()).toBe(true);
    });

    it("hides the data view from users who cannot edit", async () => {
        vi.mocked(fetchReportContext).mockResolvedValue(
            makeContext({ can_edit: false }),
        );
        const wrapper = mountReport();
        await flushPromises();

        expect(tabLabels(wrapper)).toEqual(["Report", "Graph"]);
    });

    it("renders configured summary lines from the resource data", async () => {
        const wrapper = mountReport({
            ...REPORT_CONFIG,
            header: { summary: [{ node_alias: "name_content" }] },
        });
        await flushPromises();

        expect(wrapper.find("dt").text()).toBe("Name");
        expect(wrapper.find("dd").text()).toBe("Cobalt blue");
    });

    it("renders full-width views without a splitter", async () => {
        const wrapper = mountReport();
        await flushPromises();

        await wrapper.findAll('[role="tab"]')[2].trigger("click");

        expect(wrapper.find(".resource-report-splitter").exists()).toBe(false);
        expect(wrapper.find(".resource-report-full-pane").text()).toBe(
            "A graph view of this resource is coming soon.",
        );
    });

    it("lets reviewers change the lifecycle state", async () => {
        const wrapper = mountReport();
        await flushPromises();

        await wrapper
            .find(".report-header-lifecycle-actions button")
            .trigger("click");
        await flushPromises();

        expect(updateLifecycleState).toHaveBeenCalledWith(
            "resource-id",
            "active",
        );
        expect(fetchReportContext).toHaveBeenCalledTimes(2);
    });

    it("hides lifecycle actions from users who are not reviewers", async () => {
        vi.mocked(fetchReportContext).mockResolvedValue(
            makeContext({ is_reviewer: false }),
        );
        const wrapper = mountReport();
        await flushPromises();

        expect(wrapper.find(".report-header-lifecycle-actions").exists()).toBe(
            false,
        );
    });

    it("reports a failed lifecycle change", async () => {
        vi.mocked(updateLifecycleState).mockRejectedValue(
            new Error("Permission Denied"),
        );
        const wrapper = mountReport();
        await flushPromises();

        await wrapper
            .find(".report-header-lifecycle-actions button")
            .trigger("click");
        await flushPromises();

        expect(wrapper.text()).toContain(
            "Unable to change the lifecycle state: %{message}",
        );
    });

    it("reports a configuration without views", async () => {
        const wrapper = mountReport({});
        await flushPromises();

        expect(wrapper.text()).toBe("This report configuration has no views.");
    });

    it("reports report data that cannot be loaded", async () => {
        vi.mocked(fetchReportContext).mockRejectedValue(new Error("Not found"));
        const wrapper = mountReport();
        await flushPromises();

        expect(wrapper.text()).toContain(
            "Unable to load this report: %{message}",
        );
    });
});
