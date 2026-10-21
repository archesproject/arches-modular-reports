import re
from functools import cached_property

from django.core.exceptions import ValidationError
from django.utils import translation
from django.utils.translation import gettext, gettext_noop

from arches.app.models.models import (
    CardXNodeXWidget,
    FunctionXGraph,
    GraphModel,
    Node,
)
from arches.app.models.system_settings import settings

RESOURCE_REPORT_COMPONENT = "arches_modular_reports/ResourceReport/ResourceReport"
RESOURCE_INSTANCE_DATATYPES = ["resource-instance", "resource-instance-list"]
RESOURCE_REPORT_CONFIG_KEYS = {"header", "workspaces"}


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


def workspace_entry(workspace_id, component, label, description, config):
    return {
        "id": workspace_id,
        "component": component,
        "label": translated_labels(label),
        "description": translated_labels(description),
        "config": config,
    }


def drawer_entry(component, label, icon, config):
    return {
        "component": component,
        "label": translated_labels(label),
        "icon": icon,
        "config": config,
    }


def generate_resource_report_config(graph):
    report_graph = ResourceReportGraph(graph)
    related_graph_slugs = report_graph.related_graph_slugs()
    report_workspace = workspace_entry(
        "report",
        "ReportWorkspace",
        gettext_noop("Report"),
        gettext_noop("A curated summary of this resource's data"),
        {
            "tabs": [
                {
                    "label": translated_labels(gettext_noop("Overview")),
                    "sections": [
                        {
                            "label": None,
                            "icon": None,
                            "folios": [
                                {"nodegroup_alias": nodegroup_alias}
                                for nodegroup_alias in report_graph.top_level_nodegroup_aliases()
                            ],
                        }
                    ],
                }
            ],
            "home": {
                "summary": summary_entries(
                    report_graph,
                    report_graph.descriptor_node_aliases(
                        "name", "description", "map_popup"
                    ),
                ),
                "drawer": [
                    drawer_entry(
                        "EditHistoryPanel",
                        gettext_noop("Edit History"),
                        "pi pi-clock",
                        {},
                    ),
                    drawer_entry(
                        "ImagesPanel",
                        gettext_noop("Images"),
                        "pi pi-image",
                        {"images": report_graph.image_sources(related_graph_slugs)},
                    ),
                    drawer_entry(
                        "RelatedResourcesPanel",
                        gettext_noop("Related Resources"),
                        "pi pi-link",
                        {"graphs": related_graph_slugs},
                    ),
                    drawer_entry(
                        "ManagePanel", gettext_noop("Manage"), "pi pi-cog", {}
                    ),
                ],
            },
        },
    )
    return {
        "name": "Default",
        "components": [
            {
                "component": RESOURCE_REPORT_COMPONENT,
                "config": {
                    "header": {
                        "summary": summary_entries(
                            report_graph,
                            report_graph.descriptor_node_aliases("description"),
                        ),
                        "export_formats": ["json-ld", "json", "csv"],
                    },
                    "workspaces": [
                        report_workspace,
                        workspace_entry(
                            "data",
                            "DataWorkspace",
                            gettext_noop("Data"),
                            gettext_noop(
                                "Browse and edit every field recorded on this resource"
                            ),
                            {},
                        ),
                        workspace_entry(
                            "graph",
                            "GraphWorkspace",
                            gettext_noop("Graph"),
                            gettext_noop(
                                "A visual overview of how this resource connects to its data"
                            ),
                            {},
                        ),
                    ],
                },
            }
        ],
    }


def require_keys(entry, keys, location):
    missing_keys = sorted(key for key in keys if key not in entry)
    if missing_keys:
        raise ValidationError(f"{location} is missing: {', '.join(missing_keys)}")


def validate_resource_report_config(resource_report_config, graph):
    unknown_keys = set(resource_report_config) - RESOURCE_REPORT_CONFIG_KEYS
    if unknown_keys:
        raise ValidationError(
            f"Report config has unknown keys: {', '.join(sorted(unknown_keys))}"
        )
    require_keys(resource_report_config, RESOURCE_REPORT_CONFIG_KEYS, "Report config")
    header = resource_report_config["header"]
    require_keys(header, ["summary", "export_formats"], "Header")

    all_summary_entries = list(header["summary"])
    folios = []
    panel_configs = []
    for workspace in resource_report_config["workspaces"]:
        require_keys(
            workspace,
            ["id", "component", "label", "description", "config"],
            "Workspace",
        )
        workspace_config = workspace["config"]
        if "tabs" not in workspace_config:
            continue
        require_keys(workspace_config, ["tabs", "home"], "Report workspace")
        for tab in workspace_config["tabs"]:
            require_keys(tab, ["label", "sections"], "Tab")
            for section in tab["sections"]:
                require_keys(section, ["label", "icon", "folios"], "Section")
                folios.extend(section["folios"])
        home = workspace_config["home"]
        if home is not None:
            require_keys(home, ["summary", "drawer"], "Home")
            all_summary_entries.extend(home["summary"])
            for panel in home["drawer"]:
                require_keys(
                    panel, ["component", "label", "icon", "config"], "Drawer panel"
                )
                panel_configs.append(panel["config"])

    report_graph = ResourceReportGraph(graph)
    for folio in folios:
        require_keys(folio, ["nodegroup_alias"], "Folio")
        nodegroup_alias = folio["nodegroup_alias"]
        grouping_node = report_graph.grouping_nodes_by_alias.get(nodegroup_alias)
        if grouping_node is None:
            raise ValidationError(
                f"Folio refers to an unknown nodegroup: {nodegroup_alias}"
            )
        if report_graph.parent_nodegroup_ids_by_nodegroup_id[
            grouping_node.nodegroup_id
        ]:
            raise ValidationError(
                f"Folio {nodegroup_alias} is not a top-level nodegroup; its folio renders inside its parent's"
            )
    for summary_entry in all_summary_entries:
        require_keys(summary_entry, ["node_alias", "label"], "Summary entry")
        node_alias = summary_entry["node_alias"]
        summary_node = report_graph.nodes_by_alias.get(node_alias)
        if summary_node is None or summary_node.datatype == "semantic":
            raise ValidationError(
                f"Summary must name a node that holds a value: {node_alias}"
            )
    for panel_config in panel_configs:
        for graph_slug in panel_config.get("graphs", []):
            if not GraphModel.objects.filter(slug=graph_slug, isresource=True).exists():
                raise ValidationError(
                    f"Drawer panel refers to an unknown resource model: {graph_slug}"
                )
        for image_source in panel_config.get("images", []):
            require_keys(image_source, ["model", "node"], "Image source")
            if not Node.objects.filter(
                graph__slug=image_source["model"],
                graph__isresource=True,
                alias=image_source["node"],
                datatype="file-list",
            ).exists():
                raise ValidationError(
                    f"Drawer panel refers to an unknown file node: {image_source}"
                )


def prune_resource_report_config(
    resource_report_config, readable_nodegroup_ids, nodegroup_ids_by_node_alias
):
    def is_readable(node_alias):
        return nodegroup_ids_by_node_alias.get(node_alias) in readable_nodegroup_ids

    def prune_summary(configured_summary_entries):
        return [
            summary_entry
            for summary_entry in configured_summary_entries
            if is_readable(summary_entry["node_alias"])
        ]

    header = resource_report_config["header"]
    header["summary"] = prune_summary(header["summary"])

    for workspace in resource_report_config["workspaces"]:
        workspace_config = workspace["config"]
        if "tabs" not in workspace_config:
            continue
        readable_tabs = []
        for tab in workspace_config["tabs"]:
            readable_sections = []
            for section in tab["sections"]:
                section["folios"] = [
                    folio
                    for folio in section["folios"]
                    if is_readable(folio["nodegroup_alias"])
                ]
                if section["folios"]:
                    readable_sections.append(section)
            tab["sections"] = readable_sections
            if readable_sections:
                readable_tabs.append(tab)
        workspace_config["tabs"] = readable_tabs
        home = workspace_config["home"]
        if home is not None:
            home["summary"] = prune_summary(home["summary"])
