import { beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import OpenVue from "openvue/config";
import ConfirmationService from "openvue/confirmationservice";

import DataBrowser from "@/arches_modular_reports/ResourceReport/components/DataBrowser/DataBrowser.vue";
import EditHistoryPanel from "@/arches_modular_reports/ResourceReport/components/EditHistoryPanel.vue";
import EditListTray from "@/arches_modular_reports/ResourceReport/components/EditListTray.vue";
import EditorPanel from "@/arches_modular_reports/ResourceReport/components/EditorPanel/EditorPanel.vue";
import ImagesPanel from "@/arches_modular_reports/ResourceReport/components/ImagesPanel.vue";
import KeyDataSummary from "@/arches_modular_reports/ResourceReport/components/KeyDataSummary.vue";
import ManagePanel from "@/arches_modular_reports/ResourceReport/components/ManagePanel.vue";
import RelatedResourcesPanel from "@/arches_modular_reports/ResourceReport/components/RelatedResourcesPanel.vue";
import ReportFolio from "@/arches_modular_reports/ResourceReport/components/ReportFolio.vue";
import ReportDrawer from "@/arches_modular_reports/ResourceReport/components/ReportDrawer.vue";
import ReportHeader from "@/arches_modular_reports/ResourceReport/components/ReportHeader.vue";
import ReportPlaceholder from "@/arches_modular_reports/ResourceReport/components/ReportPlaceholder.vue";
import ReportSection from "@/arches_modular_reports/ResourceReport/components/ReportSection.vue";
import ReportStack from "@/arches_modular_reports/ResourceReport/components/ReportStack.vue";
import ReportTabs from "@/arches_modular_reports/ResourceReport/components/ReportTabs.vue";
import SplitPane from "@/arches_modular_reports/ResourceReport/components/SplitPane.vue";
import WorkspaceTabs from "@/arches_modular_reports/ResourceReport/components/WorkspaceTabs.vue";
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
import { EMPTY_VALUE } from "@/arches_modular_reports/ResourceReport/constants.ts";

import type { Component } from "vue";
import type { DOMWrapper, VueWrapper } from "@vue/test-utils";
import type {
    CardXNodeXWidgetData,
    NodegroupWidgetConfig,
} from "@/arches_vue_components/types.ts";
import type {
    ComponentNode,
    LifecycleStateSummary,
    RelatedResourceGroup,
    ReportContext,
    ReportPermissions,
    ResourceReportConfig,
} from "@/arches_modular_reports/ResourceReport/types.ts";

const { componentsByPath } = vi.hoisted(() => ({
    componentsByPath: new Map<string, Component>(),
}));

vi.mock("@/arches_vue_components/application/generate-arches-url.ts", () => ({
    generateArchesURL: (urlName: string) => urlName,
}));

vi.mock("@/arches_modular_reports/ModularReport/utils.ts", () => ({
    loadComponent: (componentPath: string) =>
        componentsByPath.get(componentPath),
    preloadComponents: () => undefined,
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

const GenericCardStub = {
    name: "GenericCard",
    props: ["tileData", "mode"],
    emits: ["update:tileData"],
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
    part_notes: {
        parent_nodegroup_alias: "parts",
        cardinality: "n",
        is_writable: true,
        card: null,
        card_x_node_x_widgets: [makeWidget("part_note_content", "Part note")],
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

const COMPONENTS_PATH = "arches_modular_reports/ResourceReport/components";

const REPORT_COMPONENTS: Record<string, Component> = {
    "DataBrowser/DataBrowser": DataBrowser,
    EditHistoryPanel,
    EditListTray,
    "EditorPanel/EditorPanel": EditorPanel,
    ImagesPanel,
    KeyDataSummary,
    ManagePanel,
    RelatedResourcesPanel,
    ReportDrawer,
    ReportFolio,
    ReportHeader,
    ReportPlaceholder,
    ReportSection,
    ReportStack,
    ReportTabs,
    SplitPane,
    WorkspaceTabs,
};

for (const [componentName, reportComponent] of Object.entries(
    REPORT_COMPONENTS,
)) {
    componentsByPath.set(
        `${COMPONENTS_PATH}/${componentName}`,
        reportComponent,
    );
}

function reportNode(
    componentName: string,
    config: Record<string, unknown> = {},
): ComponentNode {
    return { component: `${COMPONENTS_PATH}/${componentName}`, config };
}

function workspaceTabs(...workspaces: ComponentNode[]): ComponentNode {
    return reportNode("WorkspaceTabs", {
        banner: [
            reportNode("ReportHeader", {
                summary: [],
                export_formats: ["json-ld"],
            }),
        ],
        components: workspaces,
    });
}

const REPORT_CONFIG: ResourceReportConfig = {
    components: [
        workspaceTabs(
            reportNode("SplitPane", {
                label: { en: "Report" },
                description: {
                    en: "A curated summary of this resource's data",
                },
                main: [reportNode("ReportTabs", { components: [] })],
                aside: [
                    reportNode("EditorPanel/EditorPanel"),
                    reportNode("ReportDrawer", { components: [], panels: [] }),
                ],
            }),
            reportNode("SplitPane", {
                label: { en: "Data" },
                requires_edit: true,
                main: [reportNode("DataBrowser/DataBrowser")],
                aside: [reportNode("EditorPanel/EditorPanel")],
            }),
            reportNode("ReportPlaceholder", {
                label: { en: "Graph" },
                icon: "pi pi-sitemap",
                message: "Graph view — coming soon",
            }),
        ),
        reportNode("EditListTray"),
    ],
};

const PIGMENTS_GROUP: RelatedResourceGroup = {
    graph_slug: "pigments",
    graph_name: "Pigments",
    iconclass: "fa fa-flask",
    color: null,
    next_cursor: "next-pigments",
    items: [
        {
            resourcexid: "smalt-relation",
            display_name: "Smalt sample",
            relationship: "Source",
            report_url: "/report/smalt",
        },
    ],
};

function folioConfig(aside: ComponentNode[]): ResourceReportConfig {
    return {
        components: [
            workspaceTabs(
                reportNode("SplitPane", {
                    label: "Report",
                    main: [
                        reportNode("ReportTabs", {
                            components: [
                                reportNode("ReportStack", {
                                    label: "Overview",
                                    components: [
                                        reportNode("ReportFolio", {
                                            nodegroup_alias: "names",
                                        }),
                                    ],
                                }),
                            ],
                        }),
                    ],
                    aside,
                }),
            ),
            reportNode("EditListTray"),
        ],
    };
}

const FOLIO_CONFIG = folioConfig([reportNode("EditorPanel/EditorPanel")]);

function drawerConfig(): ResourceReportConfig {
    return {
        components: [
            workspaceTabs(
                reportNode("SplitPane", {
                    label: "Report",
                    aside: [
                        reportNode("ReportDrawer", {
                            panels: [
                                reportNode("RelatedResourcesPanel", {
                                    label: "Related Resources",
                                    icon: "pi pi-link",
                                    graphs: ["pigments"],
                                }),
                                reportNode("ManagePanel", {
                                    label: "Manage",
                                    icon: "pi pi-cog",
                                }),
                            ],
                        }),
                    ],
                }),
            ),
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

function buttonWithText(
    wrapper: VueWrapper,
    containerSelector: string,
    label: string,
): DOMWrapper<Element> {
    const button = wrapper
        .findAll(`${containerSelector} button`)
        .find((candidate) => candidate.text() === label);
    if (button === undefined) {
        throw new Error(`No ${label} button in ${containerSelector}`);
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

        await buttonWithText(
            wrapper,
            ".report-folio-tile-actions",
            "Edit",
        ).trigger("click");
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
        await buttonWithText(
            wrapper,
            ".report-folio-tile-actions",
            "Edit",
        ).trigger("click");
        await wrapper.find(".card-stub").trigger("click");

        await buttonWithText(
            wrapper,
            ".edit-list-tray-header",
            "Apply all edits",
        ).trigger("click");
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
        await buttonWithText(
            wrapper,
            ".report-drawer-triggers",
            "Manage",
        ).trigger("click");

        await buttonWithText(wrapper, ".manage", "Delete Resource").trigger(
            "click",
        );
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

    it("shows a summary node under an unreadable parent as empty", async () => {
        const wrapper = mountReport({
            components: [
                reportNode("ReportHeader", {
                    summary: [
                        { node_alias: "part_note_content", label: "Part note" },
                    ],
                }),
                reportNode("KeyDataSummary", {
                    summary: [
                        { node_alias: "part_note_content", label: "Part note" },
                    ],
                }),
            ],
        });
        await flushPromises();

        expect(wrapper.find(".report-header-summary dd").text()).toBe(
            EMPTY_VALUE,
        );
        await wrapper.find(".key-data-summary button").trigger("click");
        await flushPromises();
        expect(wrapper.find(".key-data-summary dd").text()).toBe(EMPTY_VALUE);
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
        await buttonWithText(
            wrapper,
            ".report-drawer-triggers",
            "Related Resources",
        ).trigger("click");
        await flushPromises();

        await wrapper.find(".related-resources-group button").trigger("click");
        vi.useFakeTimers();
        await wrapper.find(".related-resources-filter").setValue("sample");
        await vi.advanceTimersByTimeAsync(300);
        vi.useRealTimers();
        await flushPromises();
        finishLoadMore({
            ...PIGMENTS_GROUP,
            next_cursor: null,
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

    it("renders an empty report from an empty config", async () => {
        const wrapper = mountReport({});
        await flushPromises();

        expect(wrapper.find(".resource-report").exists()).toBe(true);
        expect(wrapper.find(".resource-report").text()).toBe("");
    });

    it("renders a report without tabs", async () => {
        const wrapper = mountReport({
            components: [
                reportNode("ReportSection", {
                    label: "Names",
                    icon: "pi pi-id-card",
                    components: [
                        reportNode("ReportFolio", { nodegroup_alias: "names" }),
                    ],
                }),
            ],
        });
        await flushPromises();

        expect(wrapper.find(".report-section-label").text()).toBe("Names");
        expect(wrapper.find(".report-folio").exists()).toBe(true);
        expect(wrapper.find(".report-tabs-list").exists()).toBe(false);
    });

    it("hides edit-only workspaces from people who cannot edit", async () => {
        vi.mocked(fetchReportContext).mockResolvedValue(
            makeContext({ can_edit: false }),
        );
        const wrapper = mountReport();
        await flushPromises();

        expect(wrapper.findAll(".workspace-tabs-strip .p-tab")).toHaveLength(2);
        expect(wrapper.find(".workspace-tabs-strip").text()).not.toContain(
            "Data",
        );
    });

    it("offers editing only when an editor is declared", async () => {
        const wrapper = mountReport(folioConfig([]));
        await flushPromises();

        expect(wrapper.find(".report-folio").exists()).toBe(true);
        expect(wrapper.find(".report-folio-tile-actions").exists()).toBe(false);
    });
});
