import { beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import OpenVue from "openvue/config";
import ConfirmationService from "openvue/confirmationservice";

import DataBrowser from "@/arches_modular_reports/ResourceReport/components/DataBrowser/DataBrowser.vue";
import EditHistoryPanel from "@/arches_modular_reports/ResourceReport/components/EditHistoryPanel.vue";
import EditListTray from "@/arches_modular_reports/ResourceReport/components/EditListTray.vue";
import EditorPanel from "@/arches_modular_reports/ResourceReport/components/EditorPanel/EditorPanel.vue";
import FieldFolio from "@/arches_modular_reports/ResourceReport/components/FieldFolio.vue";
import ImagesPanel from "@/arches_modular_reports/ResourceReport/components/ImagesPanel.vue";
import ManagePanel from "@/arches_modular_reports/ResourceReport/components/ManagePanel.vue";
import RecordSummaryPanel from "@/arches_modular_reports/ResourceReport/components/RecordSummaryPanel.vue";
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
    fetchEditHistory,
    fetchResource,
    fetchResourceCopies,
    fetchResourceImages,
    fetchRelatedResourceGroup,
    fetchRelatedResourceGroups,
    fetchReportContext,
    saveResourceChanges,
    updateLifecycleState,
} from "@/arches_modular_reports/ResourceReport/api.ts";
import { EMPTY_VALUE } from "@/arches_modular_reports/ResourceReport/constants.ts";
import { fetchTileData } from "@/arches_vue_components/generics/GenericCard/api.ts";

import type { Component } from "vue";
import type { DOMWrapper, VueWrapper } from "@vue/test-utils";
import type {
    AliasedNodeData,
    CardXNodeXWidgetData,
    NodegroupWidgetConfig,
} from "@/arches_vue_components/types.ts";
import type {
    ComponentNode,
    EditHistoryEntry,
    LifecycleStateSummary,
    RelatedResourceGroup,
    ReportContext,
    ReportPermissions,
    ResourceImage,
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

vi.mock("@/arches_vue_components/generics/GenericCard/api.ts", () => ({
    fetchTileData: vi.fn(() =>
        Promise.resolve({
            aliased_data: {
                owner_content: {
                    display_value: "",
                    node_value: null,
                    details: [],
                },
            },
            nodegroup: "owners-nodegroup",
            parenttile: null,
            provisionaledits: null,
            resourceinstance: "",
            sortorder: 0,
            tileid: null,
        }),
    ),
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
        languages: { en: "English", de: "German" },
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

const OWNER_WIDGET = makeWidget("owner_content", "Owner");

const NODEGROUP_WIDGET_CONFIGS: Record<string, NodegroupWidgetConfig> = {
    names: {
        parent_nodegroup_alias: null,
        cardinality: "n",
        is_writable: true,
        card: makeWidget("name_content", "Name").card,
        card_x_node_x_widgets: [makeWidget("name_content", "Name")],
    },
    owners: {
        parent_nodegroup_alias: null,
        cardinality: "1",
        is_writable: true,
        card: {
            ...OWNER_WIDGET.card,
            name: "Current Owner",
            sortorder: 1,
            cardid: "owners-card",
            nodegroup_id: "owners-nodegroup",
        },
        card_x_node_x_widgets: [
            {
                ...OWNER_WIDGET,
                node: { ...OWNER_WIDGET.node, isrequired: true },
            },
        ],
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
    FieldFolio,
    ImagesPanel,
    ManagePanel,
    RecordSummaryPanel,
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

function recordSummaryConfig(): ResourceReportConfig {
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
                                        reportNode("ReportSection", {
                                            label: "Names & Identifiers",
                                            components: [
                                                reportNode("ReportFolio", {
                                                    nodegroup_alias: "names",
                                                }),
                                            ],
                                        }),
                                        reportNode("ReportSection", {
                                            label: "Location & Ownership",
                                            components: [
                                                reportNode("FieldFolio", {
                                                    nodegroup_alias: "owners",
                                                }),
                                            ],
                                        }),
                                    ],
                                }),
                            ],
                        }),
                    ],
                }),
                reportNode("SplitPane", {
                    label: "Data",
                    requires_edit: true,
                    aside_size: 60,
                    main: [reportNode("DataBrowser/DataBrowser")],
                    aside: [
                        reportNode("EditorPanel/EditorPanel"),
                        reportNode("RecordSummaryPanel"),
                    ],
                    aside_footer: [reportNode("EditListTray")],
                }),
            ),
        ],
    };
}

async function openDataWorkspace(attachTo?: HTMLElement): Promise<VueWrapper> {
    const wrapper = mountReport(recordSummaryConfig(), attachTo);
    await flushPromises();
    const dataTab = wrapper
        .findAll(".workspace-tabs-strip .p-tab")
        .find((tab) => tab.text() === "Data");
    if (dataTab === undefined) {
        throw new Error("No Data workspace tab");
    }
    await dataTab.trigger("click");
    await flushPromises();
    return wrapper;
}

function summaryFacts(wrapper: VueWrapper): Record<string, string> {
    return Object.fromEntries(
        wrapper
            .findAll(".record-summary-panel-fact")
            .map((fact) => [fact.find("dt").text(), fact.find("dd").text()]),
    );
}

function summaryEmptyCards(
    wrapper: VueWrapper,
): { group: string; cards: { name: string; isRequired: boolean }[] }[] {
    return wrapper.findAll(".record-summary-panel-group").map((group) => ({
        group: group.find(".record-summary-panel-group-label").text(),
        cards: group.findAll(".record-summary-panel-card").map((card) => ({
            name: card.find(".record-summary-panel-card-name").text(),
            isRequired: card.find(".record-summary-panel-required").exists(),
        })),
    }));
}

function countedDrawerConfig(): ResourceReportConfig {
    return {
        components: [
            workspaceTabs(
                reportNode("SplitPane", {
                    label: "Report",
                    aside: [
                        reportNode("ReportDrawer", {
                            panels: [
                                reportNode("EditHistoryPanel", {
                                    label: "Edit History",
                                    requires_edit: true,
                                }),
                                reportNode("ImagesPanel", {
                                    label: "Images",
                                    images: [
                                        {
                                            model: "digital_resources",
                                            node: "file",
                                        },
                                    ],
                                }),
                                reportNode("RelatedResourcesPanel", {
                                    label: "Related Resources",
                                    graphs: ["pigments"],
                                }),
                                reportNode("ManagePanel", { label: "Manage" }),
                            ],
                        }),
                    ],
                }),
            ),
        ],
    };
}

const NAME_EDIT: EditHistoryEntry = {
    editlogid: "edit-log-1",
    edit_type: "tile edit",
    timestamp: "2026-11-13T10:00:00Z",
    user: "Ada Lovelace",
    card_name: "Names",
    values: [
        {
            node_alias: "name_content",
            before: "Cobalt",
            after: "Cobalt blue",
            changed: true,
        },
        {
            node_alias: "part_note_content",
            before: "Dry pigment",
            after: "Dry pigment",
            changed: false,
        },
    ],
};

function makeImage(imageName: string): ResourceImage {
    return {
        url: `/files/${imageName}.jpg`,
        caption: imageName,
        alt_text: `Photo of ${imageName}`,
        resourceinstanceid: "resource-id",
        resource_name: "Cobalt blue",
        graph_name: "Reference and Sample Collection Item",
        report_url: "/report/resource-id",
    };
}

// Attach to the document when a test checks where focus lands.
// The resource with its name stored per language, as the text widget saves
// it; the display value carries only the reader's language.
function resourceNamed(
    nameByLanguage: Record<string, { value: string; direction: "ltr" }>,
): typeof RESOURCE {
    const [nameTile] = RESOURCE.aliased_data.names;
    return {
        ...RESOURCE,
        aliased_data: {
            names: [
                {
                    ...nameTile,
                    aliased_data: {
                        name_content: {
                            display_value: nameByLanguage.en?.value ?? "",
                            node_value: nameByLanguage,
                            details: [],
                        },
                    },
                },
            ],
        },
    } as unknown as typeof RESOURCE;
}

function widgetDisplayValues(wrapper: VueWrapper): string[] {
    return wrapper
        .findAllComponents(GenericWidgetStub)
        .map(
            (widgetStub) =>
                (widgetStub.props("aliasedNodeData") as AliasedNodeData)
                    .display_value,
        );
}

function mountReport(
    config: ResourceReportConfig = REPORT_CONFIG,
    attachTo?: HTMLElement,
): VueWrapper {
    return mount(ResourceReport, {
        attachTo,
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
    await drawerTrigger(wrapper, "Manage").trigger("click");
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

// The switch holds both labels so its width never changes; one is shown.
function shownLabel(editLinksSwitch: DOMWrapper<Element>): string {
    return editLinksSwitch
        .find(".workspace-tabs-edit-links-label-current")
        .text();
}

// Matches on the label alone, since a trigger may also show a count badge.
function drawerTrigger(
    wrapper: VueWrapper,
    label: string,
): DOMWrapper<Element> {
    const trigger = wrapper
        .findAll(".report-drawer-triggers button")
        .find(
            (candidate) => candidate.find(".p-button-label").text() === label,
        );
    if (trigger === undefined) {
        throw new Error(`No ${label} drawer trigger`);
    }
    return trigger;
}

describe("ResourceReport", () => {
    beforeEach(() => {
        vi.clearAllMocks();
        localStorage.clear();
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

    it("widens the aside while the editor is open", async () => {
        const wrapper = mountReport(FOLIO_CONFIG);
        await flushPromises();
        const asideStyle = (): string =>
            wrapper.find(".split-pane-aside").attributes("style") ?? "";
        expect(asideStyle()).toContain("40%");

        await buttonWithText(
            wrapper,
            ".report-folio-tile-actions",
            "Edit",
        ).trigger("click");
        await flushPromises();
        expect(asideStyle()).toContain("60%");

        await wrapper.find(".editor-panel-close").trigger("click");
        await flushPromises();
        expect(asideStyle()).toContain("40%");
    });

    it("discards every pending edit only once the discard is confirmed", async () => {
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
            ".edit-list-tray-actions",
            "Cancel all edits",
        ).trigger("click");
        await flushPromises();

        const dialog = document.body.querySelector(".alert-dialog");
        expect(dialog?.getAttribute("role")).toBe("alertdialog");
        expect(dialog?.textContent).toContain("Discard all changes?");
        expect(document.activeElement?.textContent?.trim()).toBe(
            "Keep editing",
        );

        (document.activeElement as HTMLButtonElement).click();
        await flushPromises();
        expect(wrapper.find(".edit-list-tray").exists()).toBe(true);

        await buttonWithText(
            wrapper,
            ".edit-list-tray-actions",
            "Cancel all edits",
        ).trigger("click");
        await flushPromises();
        const discardButton = [
            ...document.body.querySelectorAll(".alert-dialog button"),
        ].find((button) => button.textContent?.trim() === "Discard all");
        (discardButton as HTMLButtonElement).click();
        await flushPromises();

        expect(wrapper.find(".edit-list-tray").exists()).toBe(false);

        wrapper.unmount();
    });

    it("puts the resource header above the workspace tabs", async () => {
        const wrapper = mountReport(REPORT_CONFIG);
        await flushPromises();

        const header = wrapper.find(".workspace-tabs-header");
        expect(
            header
                .findAll(":scope > *")
                .map((child) =>
                    child
                        .classes()
                        .find((className) =>
                            ["report-header", "workspace-tabs-bar"].includes(
                                className,
                            ),
                        ),
                ),
        ).toEqual(["report-header", "workspace-tabs-bar"]);
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
        await drawerTrigger(wrapper, "Manage").trigger("click");
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

    it("words an empty folio the same way whatever the card is called", async () => {
        vi.mocked(fetchResource).mockResolvedValue({
            ...RESOURCE,
            aliased_data: { names: [] },
        });
        const wrapper = mountReport(FOLIO_CONFIG);
        await flushPromises();

        expect(wrapper.find(".report-folio-empty-message").text()).toBe(
            "Nothing recorded for %{name}.",
        );
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

    it("shows a value entered in another language, naming the language", async () => {
        vi.mocked(fetchResource).mockResolvedValue(
            resourceNamed({
                en: { value: "", direction: "ltr" },
                de: { value: "Mythische Figur", direction: "ltr" },
            }),
        );
        const wrapper = mountReport(FOLIO_CONFIG);
        await flushPromises();

        expect(wrapper.find(".report-folio-empty-message").exists()).toBe(
            false,
        );
        expect(widgetDisplayValues(wrapper)).toEqual(["Mythische Figur"]);
        expect(
            wrapper.findAll(".language-name").map((pill) => pill.text()),
        ).toEqual(["German"]);
        expect(
            wrapper.find(".node-value-language-text").attributes("lang"),
        ).toBe("de");
    });

    it("lists the reader's language first, unnamed, then the others", async () => {
        vi.mocked(fetchResource).mockResolvedValue(
            resourceNamed({
                de: { value: "Kobaltblau", direction: "ltr" },
                en: { value: "Cobalt blue", direction: "ltr" },
            }),
        );
        const wrapper = mountReport(FOLIO_CONFIG);
        await flushPromises();

        expect(widgetDisplayValues(wrapper)).toEqual([
            "Cobalt blue",
            "Kobaltblau",
        ]);
        expect(
            wrapper.findAll(".language-name").map((pill) => pill.text()),
        ).toEqual(["German"]);
    });

    it("shows a value in the reader's language alone without naming it", async () => {
        vi.mocked(fetchResource).mockResolvedValue(
            resourceNamed({
                en: { value: "Cobalt blue", direction: "ltr" },
                de: { value: "", direction: "ltr" },
            }),
        );
        const wrapper = mountReport(FOLIO_CONFIG);
        await flushPromises();

        expect(widgetDisplayValues(wrapper)).toEqual(["Cobalt blue"]);
        expect(wrapper.find(".language-name").exists()).toBe(false);
    });

    it("lets an editor hide the report's edit links, and remembers it", async () => {
        const wrapper = mountReport(FOLIO_CONFIG);
        await flushPromises();
        const editLinksSwitch = wrapper.find(".workspace-tabs-edit-links");
        expect(editLinksSwitch.attributes("aria-checked")).toBe("true");
        expect(shownLabel(editLinksSwitch)).toBe("Edit links: On");
        expect(wrapper.find(".report-folio-tile-actions").exists()).toBe(true);

        await editLinksSwitch.trigger("click");

        expect(editLinksSwitch.attributes("aria-checked")).toBe("false");
        expect(shownLabel(editLinksSwitch)).toBe("Edit links: Off");
        expect(wrapper.find(".report-folio-tile-actions").exists()).toBe(false);
        wrapper.unmount();

        const remounted = mountReport(FOLIO_CONFIG);
        await flushPromises();
        expect(shownLabel(remounted.find(".workspace-tabs-edit-links"))).toBe(
            "Edit links: Off",
        );
        expect(remounted.find(".report-folio-tile-actions").exists()).toBe(
            false,
        );

        await remounted.find(".workspace-tabs-edit-links").trigger("click");

        expect(remounted.find(".report-folio-tile-actions").exists()).toBe(
            true,
        );
    });

    it("offers the edit links switch only to editors, beside folios", async () => {
        const folioReport = mountReport(FOLIO_CONFIG);
        const reportWithoutFolios = mountReport();
        await flushPromises();
        expect(folioReport.find(".workspace-tabs-edit-links").exists()).toBe(
            true,
        );
        expect(
            reportWithoutFolios.find(".workspace-tabs-edit-links").exists(),
        ).toBe(false);

        vi.mocked(fetchReportContext).mockResolvedValue(
            makeContext({ can_edit: false }),
        );
        const readerReport = mountReport(FOLIO_CONFIG);
        await flushPromises();
        expect(readerReport.find(".workspace-tabs-edit-links").exists()).toBe(
            false,
        );
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
        await drawerTrigger(wrapper, "Related Resources").trigger("click");
        await flushPromises();

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
        expect(wrapper.find(".related-resources-empty").exists()).toBe(false);
    });

    it("lists models with nothing related on one line", async () => {
        vi.mocked(fetchRelatedResourceGroups).mockResolvedValue([
            PIGMENTS_GROUP,
            {
                ...PIGMENTS_GROUP,
                graph_slug: "places",
                graph_name: "Places",
                next_cursor: null,
                items: [],
            },
            {
                ...PIGMENTS_GROUP,
                graph_slug: "groups",
                graph_name: "Groups",
                next_cursor: null,
                items: [],
            },
        ]);
        const wrapper = mountReport(drawerConfig());
        await flushPromises();
        await drawerTrigger(wrapper, "Related Resources").trigger("click");
        await flushPromises();

        expect(
            wrapper
                .findAll(".related-resources-group-label")
                .map((label) => label.text()),
        ).toEqual(["Pigments"]);
        const emptyMessages = wrapper.findAll(".related-resources-empty");
        expect(emptyMessages).toHaveLength(1);
        expect(emptyMessages[0].text()).toBe("No related %{models}.");
    });

    it("says so when nothing at all is related", async () => {
        vi.mocked(fetchRelatedResourceGroups).mockResolvedValue([
            { ...PIGMENTS_GROUP, next_cursor: null, items: [] },
        ]);
        const wrapper = mountReport(drawerConfig());
        await flushPromises();
        await drawerTrigger(wrapper, "Related Resources").trigger("click");
        await flushPromises();

        expect(wrapper.find(".related-resources-group").exists()).toBe(false);
        expect(wrapper.find(".related-resources-empty").text()).toBe(
            "No related resources.",
        );
    });

    it("shows how many entries each drawer panel holds", async () => {
        vi.mocked(fetchEditHistory).mockResolvedValue({
            results: [NAME_EDIT, { ...NAME_EDIT, editlogid: "edit-log-2" }],
            next_cursor: null,
        });
        vi.mocked(fetchResourceImages).mockResolvedValue({
            images: [makeImage("smalt")],
            next_cursor: "more-images",
        });
        vi.mocked(fetchRelatedResourceGroups).mockResolvedValue([
            { ...PIGMENTS_GROUP, next_cursor: null },
        ]);
        const wrapper = mountReport(countedDrawerConfig());
        await flushPromises();

        function badgeText(label: string): string | null {
            const badge = drawerTrigger(wrapper, label).find(".p-badge");
            return badge.exists() ? badge.text() : null;
        }
        expect(badgeText("Edit History")).toBe("2");
        // A further page exists, so the count reads as a lower bound.
        expect(badgeText("Images")).toBe("%{count}+");
        expect(badgeText("Related Resources")).toBe("1");
        expect(badgeText("Manage")).toBeNull();
    });

    it("shows no count for a panel whose count fails to load", async () => {
        vi.mocked(fetchRelatedResourceGroups).mockRejectedValue(
            new Error("Offline"),
        );
        const wrapper = mountReport(drawerConfig());
        await flushPromises();

        expect(
            drawerTrigger(wrapper, "Related Resources")
                .find(".p-badge")
                .exists(),
        ).toBe(false);
    });

    it("recounts the drawer panels once edits are applied", async () => {
        vi.mocked(fetchRelatedResourceGroups).mockResolvedValue([
            { ...PIGMENTS_GROUP, next_cursor: null },
        ]);
        vi.mocked(saveResourceChanges).mockResolvedValue(RESOURCE);
        const wrapper = mountReport(
            folioConfig([
                reportNode("EditorPanel/EditorPanel"),
                reportNode("ReportDrawer", {
                    panels: [
                        reportNode("RelatedResourcesPanel", {
                            label: "Related Resources",
                            graphs: ["pigments"],
                        }),
                    ],
                }),
            ]),
        );
        await flushPromises();
        expect(fetchRelatedResourceGroups).toHaveBeenCalledTimes(1);

        await buttonWithText(
            wrapper,
            ".report-folio-tile-actions",
            "Edit",
        ).trigger("click");
        await wrapper.find(".card-stub").trigger("click");
        await buttonWithText(
            wrapper,
            ".edit-list-tray-actions",
            "Apply all edits",
        ).trigger("click");
        await flushPromises();

        expect(saveResourceChanges).toHaveBeenCalled();
        expect(fetchRelatedResourceGroups).toHaveBeenCalledTimes(2);
    });

    it("shows only the changed fields of an edit until asked for the rest", async () => {
        vi.mocked(fetchEditHistory).mockResolvedValue({
            results: [NAME_EDIT],
            next_cursor: null,
        });
        const wrapper = mountReport(countedDrawerConfig());
        await flushPromises();
        await drawerTrigger(wrapper, "Edit History").trigger("click");
        await flushPromises();

        // One changed field, listed under both Before and After.
        expect(wrapper.findAll(".edit-history-field")).toHaveLength(2);
        expect(wrapper.find(".edit-history-changed-marker").exists()).toBe(
            false,
        );
        const fieldsToggle = wrapper.find(".edit-history-fields-toggle");
        expect(fieldsToggle.text()).toBe("Show %{count} unchanged field");

        await fieldsToggle.trigger("click");

        expect(wrapper.findAll(".edit-history-field")).toHaveLength(4);
        expect(wrapper.findAll(".edit-history-changed-marker")).toHaveLength(2);
        expect(wrapper.find(".edit-history-changed-marker").text()).toBe(
            "(changed)",
        );
        expect(wrapper.find(".edit-history-fields-toggle").text()).toBe(
            "Show changed fields only",
        );
    });

    it("lists every field of an edit with nothing to hide", async () => {
        vi.mocked(fetchEditHistory).mockResolvedValue({
            results: [
                {
                    ...NAME_EDIT,
                    values: NAME_EDIT.values.map((value) => ({
                        ...value,
                        changed: false,
                    })),
                },
            ],
            next_cursor: null,
        });
        const wrapper = mountReport(countedDrawerConfig());
        await flushPromises();
        await drawerTrigger(wrapper, "Edit History").trigger("click");
        await flushPromises();

        expect(wrapper.findAll(".edit-history-field")).toHaveLength(4);
        expect(wrapper.find(".edit-history-fields-toggle").exists()).toBe(
            false,
        );
    });

    it("links each image at full size and leaves thumbnails unannounced", async () => {
        vi.mocked(fetchResourceImages).mockResolvedValue({
            images: [makeImage("smalt"), makeImage("cobalt")],
            next_cursor: null,
        });
        const wrapper = mountReport(countedDrawerConfig());
        await flushPromises();
        await drawerTrigger(wrapper, "Images").trigger("click");
        await flushPromises();

        const fullSizeLink = wrapper.find(".images-full-size");
        expect(fullSizeLink.attributes("href")).toBe("/files/smalt.jpg");
        expect(fullSizeLink.attributes("target")).toBe("_blank");
        expect(wrapper.find(".images-main").attributes("alt")).toBe(
            "Photo of smalt",
        );
        const thumbnails = wrapper.findAll(".images-thumbnail");
        expect(thumbnails).toHaveLength(2);
        expect(
            thumbnails.map((thumbnail) => thumbnail.attributes("alt")),
        ).toEqual(["", ""]);
    });

    it("expands the open panel across the workspace and keeps its state", async () => {
        vi.mocked(fetchRelatedResourceGroups).mockResolvedValue([
            PIGMENTS_GROUP,
        ]);
        const wrapper = mountReport(drawerConfig());
        await flushPromises();
        await drawerTrigger(wrapper, "Related Resources").trigger("click");
        await flushPromises();
        await wrapper.find(".related-resources-filter").setValue("smalt");

        const expandButton = wrapper.find(
            ".report-drawer-header button[aria-label='Expand panel']",
        );
        expect(expandButton.attributes("aria-pressed")).toBe("false");
        await expandButton.trigger("click");

        const expandedPanel = wrapper.find(
            ".split-pane-overlay-host .report-drawer-panel",
        );
        expect(expandedPanel.exists()).toBe(true);
        expect(expandedPanel.classes()).toContain(
            "report-drawer-panel-expanded",
        );
        expect(
            wrapper.find(".report-drawer-stage .report-drawer-panel").exists(),
        ).toBe(false);
        expect(
            wrapper.find<HTMLInputElement>(".related-resources-filter").element
                .value,
        ).toBe("smalt");

        await wrapper
            .find(".report-drawer-header button[aria-label='Expand panel']")
            .trigger("click");

        expect(
            wrapper.find(".report-drawer-stage .report-drawer-panel").exists(),
        ).toBe(true);
        expect(
            wrapper
                .find(".split-pane-overlay-host .report-drawer-panel")
                .exists(),
        ).toBe(false);
    });

    it("reopens a closed panel at its usual width", async () => {
        vi.mocked(fetchRelatedResourceGroups).mockResolvedValue([
            PIGMENTS_GROUP,
        ]);
        const wrapper = mountReport(drawerConfig());
        await flushPromises();
        await drawerTrigger(wrapper, "Related Resources").trigger("click");
        await wrapper
            .find(".report-drawer-header button[aria-label='Expand panel']")
            .trigger("click");
        await wrapper
            .find(".report-drawer-header button[aria-label='Close']")
            .trigger("click");
        await drawerTrigger(wrapper, "Related Resources").trigger("click");

        expect(
            wrapper.find(".report-drawer-stage .report-drawer-panel").exists(),
        ).toBe(true);
        expect(
            wrapper
                .find(".report-drawer-header button[aria-label='Expand panel']")
                .attributes("aria-pressed"),
        ).toBe("false");
    });

    it("summarizes the latest edit and which cards have data", async () => {
        vi.mocked(fetchEditHistory).mockResolvedValue({
            results: [NAME_EDIT],
            next_cursor: null,
        });
        const wrapper = await openDataWorkspace();

        expect(fetchEditHistory).toHaveBeenCalledWith("resource-id", null, "");
        const facts = summaryFacts(wrapper);
        expect(facts["Last updated"]).toBe(
            new Date(NAME_EDIT.timestamp).toLocaleString("en", {
                dateStyle: "medium",
                timeStyle: "short",
            }),
        );
        expect(facts["Updated by"]).toBe("Ada Lovelace");
        expect(facts["Cards with data"]).toBe("%{filled} of %{total}");
        expect(facts["Cards without data"]).toBe(
            "%{count}, including %{required} required",
        );
        expect(summaryEmptyCards(wrapper)).toEqual([
            {
                group: "Overview",
                cards: [{ name: "Current Owner", isRequired: true }],
            },
        ]);
    });

    it("gives the aside the share of the width its config sets", async () => {
        const wrapper = await openDataWorkspace();

        expect(wrapper.find(".split-pane-aside").attributes("style")).toContain(
            "60%",
        );
    });

    it("notes a record with no edit history", async () => {
        vi.mocked(fetchEditHistory).mockResolvedValue({
            results: [],
            next_cursor: null,
        });
        const wrapper = await openDataWorkspace();

        const facts = summaryFacts(wrapper);
        expect(facts["Last updated"]).toBe("No edits recorded");
        expect(facts["Updated by"]).toBe(EMPTY_VALUE);
    });

    it("notes when the latest edit can't be loaded", async () => {
        vi.mocked(fetchEditHistory).mockRejectedValue(new Error("Offline"));
        const wrapper = await openDataWorkspace();

        expect(summaryFacts(wrapper)["Last updated"]).toBe("Unavailable");
    });

    it("reloads the latest edit once edits are applied", async () => {
        vi.mocked(fetchEditHistory).mockResolvedValue({
            results: [NAME_EDIT],
            next_cursor: null,
        });
        vi.mocked(saveResourceChanges).mockResolvedValue(RESOURCE);
        const wrapper = await openDataWorkspace();
        expect(fetchEditHistory).toHaveBeenCalledTimes(1);

        await wrapper.find(".data-folio-toggle").trigger("click");
        await buttonWithText(wrapper, ".data-folio-tiles", "Edit").trigger(
            "click",
        );
        await wrapper.find(".card-stub").trigger("click");
        await buttonWithText(
            wrapper,
            ".edit-list-tray-actions",
            "Apply all edits",
        ).trigger("click");
        await flushPromises();

        expect(saveResourceChanges).toHaveBeenCalled();
        expect(fetchEditHistory).toHaveBeenCalledTimes(2);
    });

    it("gives way to the editor while an entry is being edited", async () => {
        const wrapper = await openDataWorkspace();
        expect(wrapper.find(".record-summary-panel").exists()).toBe(true);

        await wrapper.find(".data-folio-toggle").trigger("click");
        await buttonWithText(wrapper, ".data-folio-tiles", "Edit").trigger(
            "click",
        );

        expect(wrapper.find(".editor-panel-overlay").exists()).toBe(true);
        expect(wrapper.find(".record-summary-panel").exists()).toBe(false);

        await wrapper.find(".editor-panel-close").trigger("click");

        expect(wrapper.find(".record-summary-panel").exists()).toBe(true);
    });

    it("says so when every card has data", async () => {
        vi.mocked(fetchResource).mockResolvedValue({
            ...RESOURCE,
            aliased_data: {
                ...RESOURCE.aliased_data,
                owners: {
                    ...RESOURCE.aliased_data.names[0],
                    aliased_data: {
                        owner_content: {
                            display_value: "Getty",
                            node_value: "Getty",
                            details: [],
                        },
                    },
                    nodegroup: "owners-nodegroup",
                    tileid: "owner-tile",
                },
            },
        });
        const wrapper = await openDataWorkspace();

        expect(summaryFacts(wrapper)["Cards without data"]).toBe("0");
        expect(wrapper.find(".record-summary-panel-group").exists()).toBe(
            false,
        );
        expect(wrapper.find(".record-summary-panel-none").text()).toBe(
            "Every card has data.",
        );
    });

    it("clears the data filter from its clear button", async () => {
        const wrapper = await openDataWorkspace(document.body);
        expect(wrapper.find(".data-browser-filter-clear").exists()).toBe(false);
        vi.useFakeTimers();
        await wrapper.find(".data-browser-filter").setValue("zzz");
        await vi.advanceTimersByTimeAsync(300);
        vi.useRealTimers();
        await flushPromises();
        expect(wrapper.findAll(".data-browser-folio")).toHaveLength(0);

        await wrapper.find(".data-browser-filter-clear").trigger("click");

        const filterInput = wrapper.find<HTMLInputElement>(
            ".data-browser-filter",
        ).element;
        expect(filterInput.value).toBe("");
        expect(document.activeElement).toBe(filterInput);
        expect(wrapper.find(".data-browser-filter-clear").exists()).toBe(false);
        expect(wrapper.findAll(".data-browser-folio").length).toBeGreaterThan(
            0,
        );
        wrapper.unmount();
    });

    it("adds an entry to a card, clearing a filter that hides it", async () => {
        const wrapper = await openDataWorkspace(document.body);
        vi.useFakeTimers();
        await wrapper.find(".data-browser-filter").setValue("zzz");
        await vi.advanceTimersByTimeAsync(300);
        vi.useRealTimers();
        await flushPromises();
        expect(wrapper.findAll(".data-browser-folio")).toHaveLength(0);

        await wrapper.find(".record-summary-panel-card-name").trigger("click");
        await flushPromises();

        const folio = wrapper.findAll(".data-browser-folio")[1];
        expect(
            wrapper.find<HTMLInputElement>(".data-browser-filter").element
                .value,
        ).toBe("");
        expect(folio.text()).toContain("Current Owner");
        expect(folio.classes()).toContain("data-browser-folio-flash");
        expect(Element.prototype.scrollIntoView).toHaveBeenCalled();
        expect(fetchTileData).toHaveBeenCalledWith(expect.anything(), "owners");
        expect(wrapper.find(".card-stub").exists()).toBe(true);
        expect(wrapper.find(".record-summary-panel").exists()).toBe(false);

        wrapper.unmount();
    });
});
