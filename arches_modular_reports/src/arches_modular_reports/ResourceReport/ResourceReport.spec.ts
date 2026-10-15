import { beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import OpenVue from "openvue/config";
import ConfirmationService from "openvue/confirmationservice";

import ResourceReport from "@/arches_modular_reports/ResourceReport/ResourceReport.vue";

import {
    copyResource,
    deleteResource,
    fetchEditHistory,
    fetchResource,
    fetchReportContext,
    updateLifecycleState,
} from "@/arches_modular_reports/ResourceReport/api.ts";

import type {
    CardXNodeXWidgetData,
    NodegroupWidgetConfig,
} from "@/arches_vue_components/types.ts";
import type {
    EditHistoryPage,
    LifecycleStateSummary,
    ReportContext,
    ReportPermissions,
    ResourceReportConfig,
} from "@/arches_modular_reports/ResourceReport/types.ts";

vi.mock("@/arches_vue_components/application/generate-arches-url.ts", () => ({
    generateArchesURL: (urlName: string) => urlName,
}));

vi.mock("@/arches_modular_reports/ResourceReport/api.ts", () => ({
    copyResource: vi.fn(),
    deleteResource: vi.fn(),
    resourceReportUrl: (resourceInstanceId: string) =>
        `/report/${resourceInstanceId}`,
    searchUrl: () => "/search",
    fetchEditHistory: vi.fn(),
    fetchResource: vi.fn(),
    fetchReportContext: vi.fn(),
    updateLifecycleState: vi.fn(),
    updateResource: vi.fn(),
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

const GenericWidgetStub = {
    name: "GenericWidget",
    props: ["mode", "nodeAlias", "graphSlug", "aliasedNodeData"],
    template: "<span class='widget-stub' />",
};

const focusWidgetInputForNodeAlias = vi.fn();

const GenericCardStub = {
    name: "GenericCard",
    props: ["tileData", "mode"],
    emits: ["update:tileData"],
    methods: { focusWidgetInputForNodeAlias },
    template:
        "<button class='card-stub' @click=\"$emit('update:tileData', { ...tileData, aliased_data: { name_content: { display_value: 'Smalt', node_value: 'Smalt', details: [] } } })\" />",
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
    resourceinstanceid: "resource-id",
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

const HISTORY_PAGE: EditHistoryPage = {
    results: [
        {
            editlogid: "edit-1",
            edit_type: "tile edit",
            timestamp: "2026-10-14T10:00:00Z",
            user: "Ada Lovelace",
            card_name: "Names",
            values: [
                {
                    node_alias: "name_content",
                    label: "Name",
                    before: "Smalt",
                    after: "Cobalt blue",
                    changed: true,
                },
            ],
        },
    ],
    page: 1,
    total_count: 2,
    has_next: true,
};

function drawerConfig(): ResourceReportConfig {
    return {
        workspaces: [
            {
                id: "report",
                component: "ReportWorkspace",
                config: {
                    tabs: [],
                    home: {
                        summary: [],
                        drawer: [
                            {
                                component: "EditHistoryPanel",
                                label: "Edit History",
                                icon: "pi pi-clock",
                            },
                            {
                                component: "ManagePanel",
                                label: "Manage",
                                icon: "pi pi-cog",
                            },
                            {
                                component: "WorkflowsPanel",
                                label: "Workflows",
                                icon: "pi pi-list-check",
                            },
                        ],
                    },
                },
            },
        ],
    };
}

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
            plugins: [[OpenVue, { theme: "none" }], ConfirmationService],
            provide: { graphSlug: "reference_and_sample_collection_item" },
            stubs: {
                GenericWidget: GenericWidgetStub,
                GenericCard: GenericCardStub,
            },
        },
    });
}

function folioButton(wrapper: ReturnType<typeof mountReport>, label: string) {
    const button = wrapper
        .findAll(".report-folio-field button")
        .find((candidate) => candidate.text() === label);
    if (button === undefined) {
        throw new Error(`No ${label} button in the report folio`);
    }
    return button;
}

function drawerTrigger(wrapper: ReturnType<typeof mountReport>, label: string) {
    const trigger = wrapper
        .findAll(".home-drawer-triggers button")
        .find((candidate) => candidate.text() === label);
    if (trigger === undefined) {
        throw new Error(`No ${label} drawer trigger`);
    }
    return trigger;
}

function manageButton(wrapper: ReturnType<typeof mountReport>, label: string) {
    const button = wrapper
        .findAll(".manage button")
        .find((candidate) => candidate.text() === label);
    if (button === undefined) {
        throw new Error(`No ${label} button in the manage panel`);
    }
    return button;
}

function tabLabels(wrapper: ReturnType<typeof mountReport>): string[] {
    return wrapper.findAll('[role="tab"]').map((tab) => tab.text());
}

describe("ResourceReport", () => {
    beforeEach(() => {
        vi.clearAllMocks();
        Element.prototype.scrollIntoView = vi.fn();
        vi.mocked(fetchReportContext).mockResolvedValue(makeContext());
        vi.mocked(fetchResource).mockResolvedValue(RESOURCE);
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

        const widgets = wrapper.findAllComponents(GenericWidgetStub);
        expect(widgets).toHaveLength(1);
        expect(widgets[0].props()).toMatchObject({
            mode: "view",
            nodeAlias: "name_content",
            graphSlug: "reference_and_sample_collection_item",
        });

        await wrapper.find(".key-data-summary button").trigger("click");
        await flushPromises();

        expect(Element.prototype.scrollIntoView).toHaveBeenCalledWith({
            block: "center",
        });
        expect(wrapper.find(".report-workspace-folio").classes()).toContain(
            "report-workspace-folio-flash",
        );
    });

    it("edits a tile from a report folio and lists the change in the tray", async () => {
        const wrapper = mountReport({
            workspaces: [
                {
                    id: "report",
                    component: "ReportWorkspace",
                    config: {
                        tabs: [
                            {
                                sections: [
                                    { folios: [{ nodegroup_alias: "names" }] },
                                ],
                            },
                        ],
                        home: { summary: [] },
                    },
                },
            ],
        });
        await flushPromises();

        await folioButton(wrapper, "Edit").trigger("click");
        expect(wrapper.find(".key-data-summary").exists()).toBe(false);

        await folioButton(wrapper, "Edit").trigger("click");
        await flushPromises();
        expect(focusWidgetInputForNodeAlias).toHaveBeenCalledWith(
            "name_content",
        );

        await folioButton(wrapper, "Delete").trigger("click");
        expect(
            wrapper.findComponent(GenericCardStub).props("tileData")
                .aliased_data.name_content.display_value,
        ).toBe("");

        await wrapper.find(".card-stub").trigger("click");
        expect(wrapper.find(".edit-list-tray-entry").text()).toContain(
            "Edited",
        );

        await wrapper
            .find('.edit-list-tray-entry [aria-label="Discard change"]')
            .trigger("click");
        expect(wrapper.find(".edit-list-tray").exists()).toBe(false);
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

    it("opens edit history from the home drawer, filters it and loads more", async () => {
        vi.mocked(fetchEditHistory).mockResolvedValue(HISTORY_PAGE);
        const wrapper = mountReport(drawerConfig());
        await flushPromises();

        await drawerTrigger(wrapper, "Edit History").trigger("click");
        await flushPromises();
        expect(wrapper.find(".home-drawer-crumb").text()).toContain(
            "Cobalt blue",
        );
        expect(wrapper.find(".home-drawer-crumb").text()).toContain(
            "Edit History",
        );
        expect(wrapper.find(".edit-history-entry").text()).toContain(
            "Ada Lovelace",
        );
        expect(
            wrapper
                .findAll(".edit-history-field-changed dd")
                .map((value) => value.text()),
        ).toEqual(["Smalt", "Cobalt blue"]);
        expect(fetchEditHistory).toHaveBeenLastCalledWith("resource-id", 1, "");

        vi.useFakeTimers();
        await wrapper.find(".edit-history-filter").setValue("ada");
        await vi.advanceTimersByTimeAsync(300);
        vi.useRealTimers();
        await flushPromises();
        expect(fetchEditHistory).toHaveBeenLastCalledWith(
            "resource-id",
            1,
            "ada",
        );

        await wrapper.find(".edit-history > button").trigger("click");
        await flushPromises();
        expect(fetchEditHistory).toHaveBeenLastCalledWith(
            "resource-id",
            2,
            "ada",
        );
        expect(wrapper.findAll(".edit-history-entry")).toHaveLength(2);

        await drawerTrigger(wrapper, "Edit History").trigger("click");
        expect(wrapper.find(".home-drawer-panel").exists()).toBe(false);
    });

    it("hides edit history from users who cannot edit and flags unknown panels", async () => {
        vi.mocked(fetchReportContext).mockResolvedValue(
            makeContext({ can_edit: false }),
        );
        const wrapper = mountReport(drawerConfig());
        await flushPromises();

        expect(
            wrapper
                .findAll(".home-drawer-triggers button")
                .map((trigger) => trigger.text()),
        ).toEqual(["Manage", "Workflows"]);

        await drawerTrigger(wrapper, "Workflows").trigger("click");
        expect(wrapper.find(".home-drawer-body").text()).toContain(
            "This panel is not available",
        );
    });

    it("copies, prints and confirms deletion from the manage panel", async () => {
        vi.mocked(copyResource).mockResolvedValue("copy-id");
        vi.mocked(deleteResource).mockRejectedValue(
            new Error("Unable to Delete Resource"),
        );
        const print = vi.spyOn(window, "print").mockImplementation(() => {});
        const wrapper = mountReport(drawerConfig());
        await flushPromises();
        await drawerTrigger(wrapper, "Manage").trigger("click");

        await manageButton(wrapper, "Create Copy").trigger("click");
        await flushPromises();
        expect(copyResource).toHaveBeenCalledWith("resource-id");
        expect(wrapper.find('.manage a[href="/report/copy-id"]').exists()).toBe(
            true,
        );

        await manageButton(wrapper, "Print").trigger("click");
        expect(print).toHaveBeenCalled();

        await manageButton(wrapper, "Delete Resource").trigger("click");
        await flushPromises();
        expect(deleteResource).not.toHaveBeenCalled();
        const acceptButton = [...document.body.querySelectorAll("button")].find(
            (button) =>
                button.textContent?.trim() === "Delete Resource" &&
                !wrapper.element.contains(button),
        );
        acceptButton?.click();
        await flushPromises();
        expect(deleteResource).toHaveBeenCalledWith("resource-id");
        expect(wrapper.find(".manage").text()).toContain(
            "Unable to Delete Resource",
        );

        print.mockRestore();
        wrapper.unmount();
    });
});
