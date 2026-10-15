import { beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import OpenVue from "openvue/config";
import ConfirmationService from "openvue/confirmationservice";

import ResourceReport from "@/arches_modular_reports/ResourceReport/ResourceReport.vue";

import {
    deleteResource,
    fetchResource,
    fetchRelatedResourceGroup,
    fetchRelatedResourceGroups,
    fetchReportContext,
    updateLifecycleState,
    updateResource,
} from "@/arches_modular_reports/ResourceReport/api.ts";

import type { DOMWrapper, VueWrapper } from "@vue/test-utils";
import type {
    CardXNodeXWidgetData,
    NodegroupWidgetConfig,
} from "@/arches_vue_components/types.ts";
import type {
    LifecycleStateSummary,
    RelatedResourceGroup,
    ReportContext,
    ReportPermissions,
    ResourceReportConfig,
} from "@/arches_modular_reports/ResourceReport/types.ts";

vi.mock("@/arches_vue_components/application/generate-arches-url.ts", () => ({
    generateArchesURL: (urlName: string) => urlName,
}));

vi.mock("@/arches_modular_reports/ModularReport/utils.ts", () => ({
    loadComponent: vi.fn(),
}));

vi.mock("@/arches_modular_reports/ResourceReport/api.ts", () => ({
    copyResource: vi.fn(),
    deleteResource: vi.fn(),
    resourceReportUrl: (resourceInstanceId: string) =>
        `/report/${resourceInstanceId}`,
    searchUrl: () => "/search",
    fetchEditHistory: vi.fn(),
    fetchResource: vi.fn(),
    fetchResourceImages: vi.fn(),
    fetchRelatedResourceGroup: vi.fn(),
    fetchRelatedResourceGroups: vi.fn(),
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

const PIGMENTS_GROUP: RelatedResourceGroup = {
    graph_slug: "pigments",
    graph_name: "Pigments",
    iconclass: "fa fa-flask",
    color: null,
    total_count: 2,
    page: 1,
    has_next: true,
    items: [
        {
            resourcexid: "smalt-relation",
            display_name: "Smalt sample",
            relationship: "Source",
            report_url: "/report/smalt",
        },
    ],
};

const FOLIO_CONFIG: ResourceReportConfig = {
    workspaces: [
        {
            id: "report",
            component: "ReportWorkspace",
            config: {
                tabs: [
                    { sections: [{ folios: [{ nodegroup_alias: "names" }] }] },
                ],
                home: { summary: [] },
            },
        },
    ],
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
                                component: "RelatedResourcesPanel",
                                label: "Related Resources",
                                icon: "pi pi-link",
                                config: { graphs: ["pigments"] },
                            },
                            {
                                component: "ManagePanel",
                                label: "Manage",
                                icon: "pi pi-cog",
                            },
                        ],
                    },
                },
            },
        ],
    };
}

function mountReport(config: ResourceReportConfig = REPORT_CONFIG): VueWrapper {
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

function folioButton(wrapper: VueWrapper, label: string): DOMWrapper<Element> {
    const button = wrapper
        .findAll(".report-folio-field button")
        .find((candidate) => candidate.text() === label);
    if (button === undefined) {
        throw new Error(`No ${label} button in the report folio`);
    }
    return button;
}

function drawerTrigger(
    wrapper: VueWrapper,
    label: string,
): DOMWrapper<Element> {
    const trigger = wrapper
        .findAll(".home-drawer-triggers button")
        .find((candidate) => candidate.text() === label);
    if (trigger === undefined) {
        throw new Error(`No ${label} drawer trigger`);
    }
    return trigger;
}

function manageButton(wrapper: VueWrapper, label: string): DOMWrapper<Element> {
    const button = wrapper
        .findAll(".manage button")
        .find((candidate) => candidate.text() === label);
    if (button === undefined) {
        throw new Error(`No ${label} button in the manage panel`);
    }
    return button;
}

describe("ResourceReport", () => {
    beforeEach(() => {
        vi.clearAllMocks();
        Element.prototype.scrollIntoView = vi.fn();
        vi.mocked(fetchReportContext).mockResolvedValue(makeContext());
        vi.mocked(fetchResource).mockResolvedValue(RESOURCE);
        vi.mocked(updateLifecycleState).mockResolvedValue();
    });

    it("holds lifecycle changes while edits are pending", async () => {
        const wrapper = mountReport(FOLIO_CONFIG);
        await flushPromises();

        await folioButton(wrapper, "Edit").trigger("click");
        await wrapper.find(".card-stub").trigger("click");

        expect(
            wrapper
                .find(".report-header-lifecycle-actions button")
                .attributes("disabled"),
        ).toBeDefined();
    });

    it("holds structural edits while a save is running", async () => {
        vi.mocked(updateResource).mockReturnValueOnce(new Promise(() => {}));
        const wrapper = mountReport(FOLIO_CONFIG);
        await flushPromises();
        await folioButton(wrapper, "Edit").trigger("click");
        await wrapper.find(".card-stub").trigger("click");

        const applyButton = wrapper
            .findAll(".edit-list-tray-header button")
            .find((button) => button.text() === "Apply all");
        if (applyButton === undefined) {
            throw new Error("No Apply all button");
        }
        await applyButton.trigger("click");
        await flushPromises();

        expect(
            wrapper
                .find('.edit-list-tray-entry [aria-label="Discard change"]')
                .attributes("disabled"),
        ).toBeDefined();
    });

    it("keeps the report when refreshing it fails", async () => {
        vi.mocked(fetchReportContext)
            .mockResolvedValueOnce(makeContext())
            .mockRejectedValueOnce(new Error("Offline"));
        const wrapper = mountReport();
        await flushPromises();

        await wrapper
            .find(".report-header-lifecycle-actions button")
            .trigger("click");
        await flushPromises();

        expect(wrapper.find(".resource-report").exists()).toBe(true);
        expect(wrapper.text()).toContain("Unable to refresh this report");
    });

    it("shows interpolated text unescaped once", async () => {
        vi.mocked(fetchReportContext).mockRejectedValue(
            new Error("Smalt & Cobalt's sample"),
        );
        const wrapper = mountReport();
        await flushPromises();

        expect(wrapper.text()).toContain(
            "Unable to load this report: Smalt & Cobalt's sample",
        );
    });

    it("deletes the resource only once the deletion is confirmed", async () => {
        vi.mocked(deleteResource).mockRejectedValue(new Error("Offline"));
        const wrapper = mountReport(drawerConfig());
        await flushPromises();
        await drawerTrigger(wrapper, "Manage").trigger("click");

        await manageButton(wrapper, "Delete Resource").trigger("click");
        await flushPromises();
        expect(deleteResource).not.toHaveBeenCalled();

        const acceptButton = [...document.body.querySelectorAll("button")].find(
            (button) =>
                button.textContent?.trim() === "Delete Resource" &&
                !wrapper.element.contains(button),
        );
        if (acceptButton === undefined) {
            throw new Error("No Delete Resource button in the confirm dialog");
        }
        acceptButton.click();
        await flushPromises();
        expect(deleteResource).toHaveBeenCalledWith("resource-id");

        wrapper.unmount();
    });

    it("ignores a Load more page from a superseded filter", async () => {
        vi.mocked(fetchRelatedResourceGroups).mockResolvedValue([
            PIGMENTS_GROUP,
        ]);
        let finishLoadMore: (group: RelatedResourceGroup) => void = () =>
            undefined;
        vi.mocked(fetchRelatedResourceGroup).mockReturnValueOnce(
            new Promise((resolve) => {
                finishLoadMore = resolve;
            }),
        );
        const wrapper = mountReport(drawerConfig());
        await flushPromises();
        await drawerTrigger(wrapper, "Related Resources").trigger("click");
        await flushPromises();

        await wrapper.find(".related-resources-group button").trigger("click");
        vi.useFakeTimers();
        await wrapper.find(".related-resources-filter").setValue("sample");
        await vi.advanceTimersByTimeAsync(300);
        vi.useRealTimers();
        await flushPromises();
        finishLoadMore({
            ...PIGMENTS_GROUP,
            page: 2,
            has_next: false,
            items: [
                {
                    resourcexid: "cobalt-relation",
                    display_name: "Cobalt sample",
                    relationship: "Source",
                    report_url: "/report/cobalt",
                },
            ],
        });
        await flushPromises();

        expect(wrapper.findAll(".related-resources-item")).toHaveLength(1);
    });
});
