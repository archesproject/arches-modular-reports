import { beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import OpenVue from "openvue/config";
import ConfirmationService from "openvue/confirmationservice";

import DataBrowser from "@/arches_modular_reports/ResourceReport/components/DataBrowser/DataBrowser.vue";
import EditListTray from "@/arches_modular_reports/ResourceReport/components/EditListTray.vue";
import EditorPanel from "@/arches_modular_reports/ResourceReport/components/EditorPanel/EditorPanel.vue";
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
    copyResource,
    deleteResource,
    fetchResource,
    fetchResourceCopies,
    fetchRelatedResourceGroup,
    fetchRelatedResourceGroups,
    fetchReportContext,
    updateLifecycleState,
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
    addResourceUrl: (graphId: string) => `/add-resource/${graphId}`,
    resourceManagerUrl: () => "/resource",
    fetchEditHistory: vi.fn(),
    fetchResource: vi.fn(),
    fetchResourceCopies: vi.fn(),
    fetchResourceImages: vi.fn(),
    fetchRelatedResourceGroup: vi.fn(),
    fetchRelatedResourceGroups: vi.fn(),
    fetchReportContext: vi.fn(),
    updateLifecycleState: vi.fn(),
    saveResourceChanges: vi.fn(),
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
            graphid: "graph-id",
            name: "Reference and Sample Collection Item",
            slug: "reference_and_sample_collection_item",
            iconclass: "fa fa-asterisk",
            color: "rgba(42,157,143,0.5)",
        },
        lifecycle_state: {
            ...DRAFT,
            next_resource_instance_lifecycle_states: [ACTIVE],
            previous_resource_instance_lifecycle_states: [],
        },
        search_url: "/search",
        language: "en",
        language_dir: "ltr",
        permissions: {
            can_edit: true,
            can_delete: true,
            can_copy: true,
            can_create: true,
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
    EditListTray,
    "EditorPanel/EditorPanel": EditorPanel,
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
        banner: [reportNode("ReportHeader", { summary: [] })],
        components: workspaces,
    });
}

const REPORT_CONFIG: ResourceReportConfig = {
    components: [
        workspaceTabs(
            reportNode("SplitPane", {
                label: { en: "Report" },
                main: [reportNode("ReportTabs", { components: [] })],
                aside: [
                    reportNode("EditorPanel/EditorPanel"),
                    reportNode("ReportDrawer", { components: [], panels: [] }),
                ],
                aside_footer: [reportNode("EditListTray")],
            }),
            reportNode("SplitPane", {
                label: { en: "Data" },
                requires_edit: true,
                main: [reportNode("DataBrowser/DataBrowser")],
                aside: [reportNode("EditorPanel/EditorPanel")],
                aside_footer: [reportNode("EditListTray")],
            }),
            reportNode("ReportPlaceholder", {
                label: { en: "Graph" },
                icon: "pi pi-sitemap",
                message: "Graph view — coming soon",
            }),
        ),
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
                    aside_footer: [reportNode("EditListTray")],
                }),
            ),
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

async function openDeleteDialog(): Promise<VueWrapper> {
    const wrapper = mountReport(drawerConfig());
    await flushPromises();
    await buttonWithText(wrapper, ".report-drawer-triggers", "Manage").trigger(
        "click",
    );
    await buttonWithText(wrapper, ".manage", "Delete Resource").trigger(
        "click",
    );
    await flushPromises();
    return wrapper;
}

function dialogDeleteButton(wrapper: VueWrapper): HTMLButtonElement {
    const deleteButton = [...document.body.querySelectorAll("button")].find(
        (button) =>
            button.textContent?.trim() === "Delete Resource" &&
            !wrapper.element.contains(button),
    );
    if (deleteButton === undefined) {
        throw new Error("No Delete Resource button in the confirm dialog");
    }
    return deleteButton;
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
        vi.mocked(fetchResourceCopies).mockResolvedValue({
            default_name: "Copy of Sample",
            results: [],
            next_cursor: null,
        });
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

    it("copies the resource under the entered name and lists the copies", async () => {
        const newCopy = {
            editlogid: "edit-2",
            resourceid: "copy-2",
            name: "Second sample",
            is_deleted: false,
            report_url: "/report/copy-2",
            user: "Ada Lovelace",
            timestamp: "2026-11-13T10:00:00Z",
        };
        const deletedCopy = {
            ...newCopy,
            editlogid: "edit-1",
            resourceid: "copy-1",
            name: "First sample",
            is_deleted: true,
            report_url: null,
        };
        vi.mocked(fetchResourceCopies)
            .mockResolvedValueOnce({
                default_name: "Copy of Sample",
                results: [deletedCopy],
                next_cursor: null,
            })
            .mockResolvedValueOnce({
                default_name: "Copy of Sample",
                results: [newCopy, deletedCopy],
                next_cursor: null,
            });
        vi.mocked(copyResource).mockResolvedValue("copy-2");
        const wrapper = mountReport(drawerConfig());
        await flushPromises();
        await buttonWithText(
            wrapper,
            ".report-drawer-triggers",
            "Manage",
        ).trigger("click");
        await flushPromises();

        const nameInput = wrapper.find<HTMLInputElement>(".manage-copy-name");
        expect(nameInput.element.value).toBe("Copy of Sample");
        expect(wrapper.find(".manage-copy-deleted s").text()).toBe(
            "First sample",
        );

        await nameInput.setValue("Second sample");
        await wrapper.find(".manage-copy-form").trigger("submit");
        await flushPromises();

        expect(copyResource).toHaveBeenCalledWith(
            "resource-id",
            "Second sample",
        );
        const copyItems = wrapper.findAll(".manage-copy");
        expect(copyItems).toHaveLength(2);
        expect(copyItems[0].text()).toContain("Second sample");
        expect(copyItems[1].find(".manage-copy-deleted").exists()).toBe(true);
        expect(wrapper.find(".manage-copy-link").attributes("href")).toBe(
            "/report/copy-2",
        );

        wrapper.unmount();
    });

    it("deletes the resource only once the deletion is confirmed", async () => {
        vi.mocked(deleteResource).mockRejectedValue(new Error("Offline"));
        const wrapper = await openDeleteDialog();
        expect(deleteResource).not.toHaveBeenCalled();

        dialogDeleteButton(wrapper).click();
        await flushPromises();

        expect(deleteResource).toHaveBeenCalledWith(
            "reference_and_sample_collection_item",
            "resource-id",
        );
        expect(document.body.textContent).toContain(
            "Unable to delete this resource: %{message}",
        );
        expect(wrapper.find(".resource-report").exists()).toBe(true);

        wrapper.unmount();
    });

    it("replaces the report with a notice once the resource is deleted", async () => {
        vi.mocked(deleteResource).mockResolvedValue();
        const wrapper = await openDeleteDialog();

        dialogDeleteButton(wrapper).click();
        await flushPromises();

        expect(wrapper.find(".resource-report").exists()).toBe(false);
        expect(wrapper.find(".deleted-resource").exists()).toBe(true);
        expect(
            wrapper
                .findAll(".deleted-resource-actions a")
                .map((link) => link.attributes("href")),
        ).toEqual(["/add-resource/graph-id", "/search", "/resource"]);

        wrapper.unmount();
    });

    it("offers no create link to users who cannot create resources", async () => {
        vi.mocked(fetchReportContext).mockResolvedValue(
            makeContext({ can_create: false }),
        );
        vi.mocked(deleteResource).mockResolvedValue();
        const wrapper = await openDeleteDialog();

        dialogDeleteButton(wrapper).click();
        await flushPromises();

        expect(
            wrapper
                .findAll(".deleted-resource-actions a")
                .map((link) => link.attributes("href")),
        ).toEqual(["/search", "/resource"]);

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
            ],
        });
        await flushPromises();

        expect(wrapper.find(".report-header-summary dd").text()).toBe(
            EMPTY_VALUE,
        );
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

    it("hides models with no matches while filtering related resources", async () => {
        vi.mocked(fetchRelatedResourceGroups).mockResolvedValue([
            PIGMENTS_GROUP,
            {
                ...PIGMENTS_GROUP,
                graph_slug: "places",
                graph_name: "Places",
                next_cursor: null,
                items: [],
            },
        ]);
        const wrapper = mountReport(drawerConfig());
        await flushPromises();
        await buttonWithText(
            wrapper,
            ".report-drawer-triggers",
            "Related Resources",
        ).trigger("click");
        await flushPromises();
        expect(wrapper.findAll(".related-resources-group")).toHaveLength(2);

        vi.useFakeTimers();
        await wrapper.find(".related-resources-filter").setValue("smalt");
        await vi.advanceTimersByTimeAsync(300);
        vi.useRealTimers();
        await flushPromises();

        expect(
            wrapper
                .findAll(".related-resources-group-label")
                .map((label) => label.text()),
        ).toEqual(["Pigments"]);
    });
});
