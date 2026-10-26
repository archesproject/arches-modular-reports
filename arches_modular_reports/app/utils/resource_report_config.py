import re
from functools import cached_property

from django.core.exceptions import ValidationError
from django.utils import translation
from django.utils.translation import gettext, gettext_noop

from arches.app.models.models import (
    CardXNodeXWidget,
    DDataType,
    FunctionXGraph,
    GraphModel,
    Node,
)
from arches.app.models.system_settings import settings

RESOURCE_REPORT_COMPONENT = "arches_modular_reports/ResourceReport/ResourceReport"
RESOURCE_INSTANCE_DATATYPES = ["resource-instance", "resource-instance-list"]
REPORT_COMPONENTS_PATH = "arches_modular_reports/ResourceReport/components"
COMPONENT_NODE_KEYS = {"component", "config"}


def extract_substrings(template_string):
    pattern = r"<(.*?)>"
    substrings = re.findall(pattern, template_string)

    return substrings


def translated_labels(message):
    labels = {}
    for language in settings.LANGUAGES:
        with translation.override(language[0]):
            labels[language[0]] = gettext(message)
    return labels


def configured_graph_ids(node):
    return {graph_config["graphid"] for graph_config in node.config["graphs"]}


class ResourceReportGraph:
    def __init__(self, graph):
        self.graph = graph
        self.graph_nodes = list(graph.node_set.select_related("nodegroup"))
        self.nodes_by_alias = {
            node.alias: node for node in self.graph_nodes if node.alias
        }
        self.grouping_nodes_by_nodegroup_id = {
            node.nodegroup_id: node
            for node in self.graph_nodes
            if node.nodegroup_id == node.pk
        }
        self.grouping_nodes_by_alias = {
            node.alias: node for node in self.grouping_nodes_by_nodegroup_id.values()
        }
        self.parent_nodegroup_ids_by_nodegroup_id = {
            node.nodegroup_id: node.nodegroup.parentnodegroup_id
            for node in self.graph_nodes
            if node.nodegroup_id
        }
        self.visible_cards = graph.cardmodel_set.filter(visible=True).order_by(
            "sortorder"
        )

    @cached_property
    def node_aliases_by_nodegroup_id_and_name(self):
        return {
            (str(node.nodegroup_id), node.name): node.alias
            for node in self.graph_nodes
            if node.nodegroup_id and node.datatype != "semantic"
        }

    @cached_property
    def descriptor_types(self):
        descriptor_function = FunctionXGraph.objects.filter(
            graph=self.graph, function__functiontype="primarydescriptors"
        ).first()
        if descriptor_function and descriptor_function.config:
            return descriptor_function.config.get("descriptor_types", {})
        return {}

    @cached_property
    def hidden_node_ids(self):
        return set(
            CardXNodeXWidget.objects.filter(
                node__graph=self.graph, visible=False
            ).values_list("node_id", flat=True)
        )

    @cached_property
    def geometric_datatypes(self):
        return set(
            DDataType.objects.filter(isgeometric=True).values_list(
                "datatype", flat=True
            )
        )

    def folio_component(self, nodegroup_alias):
        grouping_node = self.grouping_nodes_by_alias[nodegroup_alias]
        value_nodes = [
            node
            for node in self.graph_nodes
            if node.nodegroup_id == grouping_node.nodegroup_id
            and node.datatype != "semantic"
            and node.pk not in self.hidden_node_ids
        ]
        geometric_nodes = [
            node for node in value_nodes if node.datatype in self.geometric_datatypes
        ]
        if geometric_nodes:
            return report_component(
                "MapFolio",
                {
                    "nodegroup_alias": nodegroup_alias,
                    "node_alias": geometric_nodes[0].alias,
                },
            )
        has_child_nodegroups = (
            grouping_node.nodegroup_id
            in self.parent_nodegroup_ids_by_nodegroup_id.values()
        )
        if (
            grouping_node.nodegroup.cardinality == "1"
            and len(value_nodes) == 1
            and not has_child_nodegroups
        ):
            return report_component("FieldFolio", {"nodegroup_alias": nodegroup_alias})
        return report_component("ReportFolio", {"nodegroup_alias": nodegroup_alias})

    def top_level_nodegroup_aliases(self):
        return [
            self.grouping_nodes_by_nodegroup_id[card.nodegroup_id].alias
            for card in self.visible_cards
            if self.parent_nodegroup_ids_by_nodegroup_id.get(card.nodegroup_id) is None
        ]

    def related_graph_slugs(self):
        linked_graph_ids = set()
        for node in self.nodes_by_alias.values():
            if node.datatype in RESOURCE_INSTANCE_DATATYPES:
                linked_graph_ids.update(configured_graph_ids(node))
        linked_graph_ids.update(
            str(graph_id)
            for graph_id in Node.objects.filter(
                datatype__in=RESOURCE_INSTANCE_DATATYPES,
                source_identifier__isnull=True,
                config__contains={"graphs": [{"graphid": str(self.graph.pk)}]},
            ).values_list("graph_id", flat=True)
        )
        related_graphs = GraphModel.objects.filter(
            pk__in=linked_graph_ids, isresource=True, source_identifier__isnull=True
        )
        return [
            graph.slug
            for graph in sorted(related_graphs, key=lambda graph: str(graph.name))
        ]

    def image_sources(self, related_graph_slugs):
        graph_slugs = [self.graph.slug] + [
            graph_slug
            for graph_slug in related_graph_slugs
            if graph_slug != self.graph.slug
        ]
        file_nodes = Node.objects.filter(
            graph__slug__in=graph_slugs,
            datatype="file-list",
            source_identifier__isnull=True,
        ).select_related("graph")
        return [
            {"model": file_node.graph.slug, "node": file_node.alias}
            for file_node in sorted(
                file_nodes,
                key=lambda file_node: (
                    graph_slugs.index(file_node.graph.slug),
                    file_node.alias,
                ),
            )
        ]

    def descriptor_node_aliases(self, *descriptor_type_names):
        node_aliases = []
        for descriptor_type_name in descriptor_type_names:
            descriptor = self.descriptor_types.get(descriptor_type_name, {})
            nodegroup_id = descriptor.get("nodegroup_id")
            if not nodegroup_id:
                continue
            for token in extract_substrings(descriptor["string_template"]):
                node_alias = self.node_aliases_by_nodegroup_id_and_name.get(
                    (nodegroup_id, token)
                )
                if node_alias and node_alias not in node_aliases:
                    node_aliases.append(node_alias)
        return node_aliases


def summary_entries(report_graph, node_aliases):
    summary_nodes = [
        report_graph.nodes_by_alias[node_alias] for node_alias in node_aliases
    ]
    widgets_by_node_id = {
        widget.node_id: widget
        for widget in CardXNodeXWidget.objects.filter(node__in=summary_nodes)
    }
    entries = []
    for node in summary_nodes:
        label = node.name
        if node.pk in widgets_by_node_id:
            label = dict(widgets_by_node_id[node.pk].label.raw_value)
        entries.append({"node_alias": node.alias, "label": label})
    return entries


def report_component(component_name, config):
    return {
        "component": f"{REPORT_COMPONENTS_PATH}/{component_name}",
        "config": config,
    }


def drawer_panel(component_name, label, icon, **config):
    return report_component(
        component_name,
        {"label": translated_labels(label), "icon": icon, **config},
    )


def generate_resource_report_config(graph):
    report_graph = ResourceReportGraph(graph)
    related_graph_slugs = report_graph.related_graph_slugs()
    report_workspace = report_component(
        "SplitPane",
        {
            "label": translated_labels(gettext_noop("Report")),
            "description": translated_labels(
                gettext_noop("A curated summary of this resource's data")
            ),
            "main": [
                report_component(
                    "ReportTabs",
                    {
                        "components": [
                            report_component(
                                "ReportStack",
                                {
                                    "label": translated_labels(
                                        gettext_noop("Overview")
                                    ),
                                    "components": [
                                        report_graph.folio_component(nodegroup_alias)
                                        for nodegroup_alias in report_graph.top_level_nodegroup_aliases()
                                    ],
                                },
                            )
                        ]
                    },
                )
            ],
            "aside": [
                report_component("EditorPanel/EditorPanel", {}),
                report_component(
                    "ReportDrawer",
                    {
                        "components": [
                            report_component(
                                "KeyDataSummary",
                                {
                                    "summary": summary_entries(
                                        report_graph,
                                        report_graph.descriptor_node_aliases(
                                            "name", "description", "map_popup"
                                        ),
                                    )
                                },
                            )
                        ],
                        "panels": [
                            drawer_panel(
                                "EditHistoryPanel",
                                gettext_noop("Edit History"),
                                "pi pi-clock",
                                requires_edit=True,
                            ),
                            drawer_panel(
                                "ImagesPanel",
                                gettext_noop("Images"),
                                "pi pi-image",
                                images=report_graph.image_sources(related_graph_slugs),
                            ),
                            drawer_panel(
                                "RelatedResourcesPanel",
                                gettext_noop("Related Resources"),
                                "pi pi-link",
                                graphs=related_graph_slugs,
                            ),
                            drawer_panel(
                                "ManagePanel", gettext_noop("Manage"), "pi pi-cog"
                            ),
                        ],
                    },
                ),
            ],
        },
    )
    data_workspace = report_component(
        "SplitPane",
        {
            "label": translated_labels(gettext_noop("Data")),
            "description": translated_labels(
                gettext_noop("Browse and edit every field recorded on this resource")
            ),
            "requires_edit": True,
            "main": [report_component("DataBrowser/DataBrowser", {})],
            "aside": [
                report_component("EditorPanel/EditorPanel", {}),
                report_component(
                    "ReportPlaceholder",
                    {
                        "icon": "pi pi-pencil",
                        "message": translated_labels(
                            gettext_noop(
                                "Select an entry in the data browser to begin editing."
                            )
                        ),
                    },
                ),
            ],
        },
    )
    graph_workspace = report_component(
        "ReportPlaceholder",
        {
            "label": translated_labels(gettext_noop("Graph")),
            "description": translated_labels(
                gettext_noop(
                    "A visual overview of how this resource connects to its data"
                )
            ),
            "icon": "pi pi-sitemap",
            "message": translated_labels(gettext_noop("Graph view — coming soon")),
        },
    )
    return {
        "name": "Default",
        "components": [
            {
                "component": RESOURCE_REPORT_COMPONENT,
                "config": {
                    "components": [
                        report_component(
                            "WorkspaceTabs",
                            {
                                "banner": [
                                    report_component(
                                        "ReportHeader",
                                        {
                                            "summary": summary_entries(
                                                report_graph,
                                                report_graph.descriptor_node_aliases(
                                                    "description"
                                                ),
                                            ),
                                        },
                                    )
                                ],
                                "components": [
                                    report_workspace,
                                    data_workspace,
                                    graph_workspace,
                                ],
                            },
                        ),
                        report_component("EditListTray", {}),
                    ]
                },
            }
        ],
    }


def require_keys(entry, keys, location):
    missing_keys = sorted(key for key in keys if key not in entry)
    if missing_keys:
        raise ValidationError(f"{location} is missing: {', '.join(missing_keys)}")


def validate_report_config_tree(value, report_graph, refers_to_report_graph=True):
    if isinstance(value, list):
        for item in value:
            validate_report_config_tree(item, report_graph, refers_to_report_graph)
        return
    if not isinstance(value, dict):
        return
    if "component" in value:
        validate_component_node(value)
    refers_to_report_graph = refers_to_report_graph and "graph_slug" not in value
    if refers_to_report_graph:
        validate_report_graph_references(value, report_graph)
    validate_other_graph_references(value)
    for child_value in value.values():
        validate_report_config_tree(child_value, report_graph, refers_to_report_graph)


def validate_component_node(component_node):
    if set(component_node) != COMPONENT_NODE_KEYS:
        raise ValidationError(
            f"Components need exactly a component path and a config: {sorted(component_node)}"
        )
    if not isinstance(component_node["component"], str):
        raise ValidationError(
            f"Component is not a string: {component_node['component']}"
        )
    if not isinstance(component_node["config"], dict):
        raise ValidationError(f"Config is not a dict: {component_node['config']}")


def validate_report_graph_references(entry, report_graph):
    nodegroup_alias = entry.get("nodegroup_alias")
    if nodegroup_alias is not None:
        nodegroup_node = report_graph.nodes_by_alias.get(nodegroup_alias)
        if nodegroup_node is None or nodegroup_node.nodegroup_id is None:
            raise ValidationError(f"Unknown nodegroup: {nodegroup_alias}")
    node_alias = entry.get("node_alias")
    if node_alias is not None:
        node = report_graph.nodes_by_alias.get(node_alias)
        if node is None or node.datatype == "semantic":
            raise ValidationError(f"Must name a node that holds a value: {node_alias}")


def validate_other_graph_references(entry):
    for graph_slug in entry.get("graphs", []):
        if not GraphModel.objects.filter(slug=graph_slug, isresource=True).exists():
            raise ValidationError(f"Unknown resource model: {graph_slug}")
    for image_source in entry.get("images", []):
        require_keys(image_source, ["model", "node"], "Image source")
        if not Node.objects.filter(
            graph__slug=image_source["model"],
            graph__isresource=True,
            alias=image_source["node"],
            datatype="file-list",
        ).exists():
            raise ValidationError(f"Unknown file node: {image_source}")
