import { beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import OpenVue from "openvue/config";

import ResourceReport from "@/arches_modular_reports/ResourceReport/ResourceReport.vue";

import { fetchModularReportResource } from "@/arches_modular_reports/ModularReport/api.ts";
import {
    fetchReportContext,
    updateLifecycleState,
} from "@/arches_modular_reports/ResourceReport/api.ts";

import type {
    CardXNodeXWidgetData,
    NodegroupWidgetConfig,
} from "@/arches_vue_components/types.ts";
import type {
    LifecycleStateSummary,
    ReportContext,
    ReportPermissions,
    ResourceReportConfig,
} from "@/arches_modular_reports/ResourceReport/types.ts";

vi.mock("@/arches_modular_reports/ModularReport/api.ts", () => ({
    fetchModularReportResource: vi.fn(),
}));

vi.mock("@/arches_modular_reports/ResourceReport/api.ts", () => ({
    fetchReportContext: vi.fn(),
    updateLifecycleState: vi.fn(),
    buildExportUrl: () => "/export",
}));

vi.mock(
    "@/arches_vue_components/stores/useNodegroupWidgetConfigStore.ts",
    () => ({
        useNodegroupWidgetConfigStore: () => ({
            fetchGraphWidgetConfigs: () =>
                Promise.resolve(NODEGROUP_WIDGET_CONFIGS),
        }),
    }),
);

const GenericFolioStub = {
    name: "GenericFolio",
    props: ["mode", "nodegroupAlias", "graphSlug", "aliasedNodegroupData"],
    template: "<div class='folio-stub' />",
};

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

function makeWidget(nodeAlias: string, label: string): CardXNodeXWidgetData {
    return {
        card: {
            name: "Names",
            sortorder: 0,
            cardid: "names-card",
            nodegroup_id: "names-nodegroup",
            nodes: [],
            visible: true,
        },
        config: {},
        id: `${nodeAlias}-widget`,
        label,
        node: {
            alias: nodeAlias,
            isrequired: false,
            nodeid: `${nodeAlias}-node`,
            datatype: "string",
            config: {},
        },
        sortorder: 0,
        visible: true,
        widget: { widgetid: "text-widget", component: "TextWidget" },
    };
}

const NODEGROUP_WIDGET_CONFIGS: Record<string, NodegroupWidgetConfig> = {
    names: {
        parent_nodegroup_alias: null,
        cardinality: "n",
        is_writable: true,
        card: null,
        card_x_node_x_widgets: [makeWidget("name_content", "Name")],
    },
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
    workspaces: [
        {
            id: "report",
            component: "ReportWorkspace",
            label: { en: "Report" },
            description: { en: "A curated summary of this resource's data" },
            config: { tabs: [], home: { summary: [], drawer: [] } },
        },
        { id: "data", component: "DataWorkspace", label: { en: "Data" } },
        { id: "graph", component: "GraphWorkspace", label: { en: "Graph" } },
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
            stubs: { GenericFolio: GenericFolioStub },
        },
    });
}

function tabLabels(wrapper: ReturnType<typeof mountReport>): string[] {
    return wrapper.findAll('[role="tab"]').map((tab) => tab.text());
}

describe("ResourceReport", () => {
    beforeEach(() => {
        vi.clearAllMocks();
        Element.prototype.scrollIntoView = vi.fn();
        vi.mocked(fetchReportContext).mockResolvedValue(makeContext());
        vi.mocked(fetchModularReportResource).mockResolvedValue(RESOURCE);
        vi.mocked(updateLifecycleState).mockResolvedValue();
    });

    it("renders the header, summary lines and every view for editors", async () => {
        const wrapper = mountReport({
            ...REPORT_CONFIG,
            header: { summary: [{ node_alias: "name_content" }] },
        });
        await flushPromises();

        expect(wrapper.find("dt").text()).toBe("Name");
        expect(wrapper.find("dd").text()).toBe("Cobalt blue");

        expect(wrapper.find("h2").text()).toBe("Cobalt blue");
        expect(tabLabels(wrapper)).toEqual(["Report", "Data", "Graph"]);
        expect(wrapper.find(".resource-report-caption").text()).toBe(
            "A curated summary of this resource's data",
        );
        expect(wrapper.find(".report-workspace").exists()).toBe(true);
    });

    it("switches between workspaces", async () => {
        const wrapper = mountReport();
        await flushPromises();

        await wrapper.findAll('[role="tab"]')[2].trigger("click");

        expect(wrapper.find(".report-workspace").exists()).toBe(false);
        expect(wrapper.find(".resource-report-workspace").text()).toBe(
            "A graph view of this resource is coming soon.",
        );
    });

    it("renders configured folios and jumps to them from the key data summary", async () => {
        const wrapper = mountReport({
            workspaces: [
                {
                    id: "report",
                    component: "ReportWorkspace",
                    config: {
                        tabs: [
                            {
                                sections: [
                                    {
                                        folios: [{ nodegroup_alias: "names" }],
                                    },
                                ],
                            },
                        ],
                        home: { summary: [{ node_alias: "name_content" }] },
                    },
                },
            ],
        });
        await flushPromises();

        const folio = wrapper.findComponent(GenericFolioStub);
        expect(folio.props()).toMatchObject({
            mode: "view",
            nodegroupAlias: "names",
            graphSlug: "reference_and_sample_collection_item",
        });
        expect(folio.props("aliasedNodegroupData")).toHaveLength(1);

        await wrapper.find(".key-data-summary button").trigger("click");
        await flushPromises();

        expect(Element.prototype.scrollIntoView).toHaveBeenCalledWith({
            block: "center",
        });
        expect(
            wrapper.find('[data-nodegroup-alias="names"]').classes(),
        ).toContain("report-workspace-folio-flash");
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

    it("reports a configuration without workspaces", async () => {
        const wrapper = mountReport({});
        await flushPromises();

        expect(wrapper.text()).toBe(
            "This report configuration has no workspaces.",
        );
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
