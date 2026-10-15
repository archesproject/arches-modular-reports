import re
from pathlib import Path

from django.core.exceptions import ValidationError
from django.utils import translation
from django.utils.translation import gettext, gettext_noop

from arches.app.models.models import FunctionXGraph, GraphModel, Node
from arches.app.models.system_settings import settings

RESOURCE_REPORT_COMPONENT = "arches_modular_reports/ResourceReport/ResourceReport"
DESCRIPTOR_TOKEN_PATTERN = re.compile(r"<([^<>]+)>")
RESOURCE_INSTANCE_DATATYPES = ["resource-instance", "resource-instance-list"]
RELATED_RESOURCES_PANEL = "RelatedResourcesPanel"


def is_resource_report_component(component_path):
    return Path(component_path).stem == Path(RESOURCE_REPORT_COMPONENT).stem


def translated_labels(message):
    labels = {}
    for language in settings.LANGUAGES:
        with translation.override(language[0]):
            labels[language[0]] = gettext(message)
    return labels


def configured_graph_ids(node):
    return {
        graph_config["graphid"]
        for graph_config in (node.config or {}).get("graphs", [])
        if graph_config.get("graphid")
    }


class ResourceReportGraph:
    def __init__(self, graph):
        self.graph = graph
        graph_nodes = list(graph.node_set.select_related("nodegroup"))
        self.nodes_by_alias = {node.alias: node for node in graph_nodes if node.alias}
        self.grouping_nodes_by_nodegroup_id = {
            node.nodegroup_id: node
            for node in graph_nodes
            if node.nodegroup_id == node.pk
        }
        self.grouping_nodes_by_alias = {
            node.alias: node for node in self.grouping_nodes_by_nodegroup_id.values()
        }
        self.parent_nodegroup_ids_by_nodegroup_id = {
            node.nodegroup_id: node.nodegroup.parentnodegroup_id
            for node in graph_nodes
            if node.nodegroup_id
        }
        self.node_aliases_by_nodegroup_id_and_name = {}
        for node in graph_nodes:
            if node.nodegroup_id:
                self.node_aliases_by_nodegroup_id_and_name[
                    (str(node.nodegroup_id), node.name)
                ] = node.alias
        self.visible_cards = sorted(
            (card for card in graph.cardmodel_set.all() if card.visible),
            key=lambda card: card.sortorder or 0,
        )
        descriptor_function = FunctionXGraph.objects.filter(
            graph=graph, function__functiontype="primarydescriptors"
        ).first()
        self.descriptor_types = {}
        if descriptor_function and descriptor_function.config:
            self.descriptor_types = descriptor_function.config.get(
                "descriptor_types", {}
            )

    def child_nodegroup_ids(self, parent_nodegroup_id):
        return [
            card.nodegroup_id
            for card in self.visible_cards
            if self.parent_nodegroup_ids_by_nodegroup_id.get(card.nodegroup_id)
            == parent_nodegroup_id
        ]

    def related_graph_slugs(self):
        linked_graph_ids = set()
        for node in self.nodes_by_alias.values():
            if node.datatype in RESOURCE_INSTANCE_DATATYPES:
                linked_graph_ids.update(configured_graph_ids(node))
        linked_graph_ids.update(
            str(node.graph_id)
            for node in Node.objects.filter(
                datatype__in=RESOURCE_INSTANCE_DATATYPES,
                source_identifier__isnull=True,
            ).only("graph_id", "config")
            if str(self.graph.pk) in configured_graph_ids(node)
        )
        related_graphs = GraphModel.objects.filter(
            pk__in=linked_graph_ids, isresource=True, source_identifier__isnull=True
        )
        return [
            graph.slug
            for graph in sorted(related_graphs, key=lambda graph: str(graph.name))
        ]

    def descriptor_node_aliases(self, *descriptor_type_names):
        node_aliases = []
        for descriptor_type_name in descriptor_type_names:
            descriptor = self.descriptor_types.get(descriptor_type_name, {})
            for token in DESCRIPTOR_TOKEN_PATTERN.findall(
                descriptor.get("string_template") or ""
            ):
                node_alias = self.descriptor_token_node_alias(
                    token, descriptor.get("nodegroup_id")
                )
                if node_alias and node_alias not in node_aliases:
                    node_aliases.append(node_alias)
        return node_aliases

    def descriptor_token_node_alias(self, token, nodegroup_id):
        if token in self.nodes_by_alias:
            return token
        return self.node_aliases_by_nodegroup_id_and_name.get(
            (str(nodegroup_id), token)
        )


def summary_entries(node_aliases):
    return [{"node_alias": node_alias, "label": None} for node_alias in node_aliases]


def build_folio_entry(report_graph, nodegroup_id):
    return {
        "nodegroup_alias": report_graph.grouping_nodes_by_nodegroup_id[
            nodegroup_id
        ].alias
    }


def workspace_entry(workspace_id, component, label, description):
    return {
        "id": workspace_id,
        "component": component,
        "label": translated_labels(label),
        "description": translated_labels(description),
    }


def drawer_entry(component, label, icon, config=None):
    entry = {"component": component, "label": translated_labels(label), "icon": icon}
    if config is not None:
        entry["config"] = config
    return entry


def generate_resource_report_config(graph):
    report_graph = ResourceReportGraph(graph)
    related_graph_slugs = report_graph.related_graph_slugs()
    report_workspace = {
        **workspace_entry(
            "report",
            "ReportWorkspace",
            gettext_noop("Report"),
            gettext_noop("A curated summary of this resource's data"),
        ),
        "config": {
            "tabs": [
                {
                    "label": translated_labels(gettext_noop("Overview")),
                    "sections": [
                        {
                            "folios": [
                                build_folio_entry(report_graph, nodegroup_id)
                                for nodegroup_id in report_graph.child_nodegroup_ids(
                                    None
                                )
                            ]
                        }
                    ],
                }
            ],
            "home": {
                "summary": summary_entries(
                    report_graph.descriptor_node_aliases(
                        "name", "description", "map_popup"
                    )
                ),
                "drawer": [
                    drawer_entry(
                        "EditHistoryPanel", gettext_noop("Edit History"), "pi pi-clock"
                    ),
                    drawer_entry("ImagesPanel", gettext_noop("Images"), "pi pi-image"),
                    drawer_entry(
                        RELATED_RESOURCES_PANEL,
                        gettext_noop("Related Resources"),
                        "pi pi-link",
                        config={"graphs": related_graph_slugs},
                    ),
                    drawer_entry("ManagePanel", gettext_noop("Manage"), "pi pi-cog"),
                ],
            },
        },
    }
    return {
        "name": "Default",
        "components": [
            {
                "component": RESOURCE_REPORT_COMPONENT,
                "config": {
                    "header": {
                        "summary": summary_entries(
                            report_graph.descriptor_node_aliases("description")
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
                        ),
                        workspace_entry(
                            "graph",
                            "GraphWorkspace",
                            gettext_noop("Graph"),
                            gettext_noop(
                                "A visual overview of how this resource connects to its data"
                            ),
                        ),
                    ],
                },
            }
        ],
    }


def iterate_folios(resource_report_config):
    for workspace in resource_report_config.get("workspaces", []):
        for tab in workspace.get("config", {}).get("tabs", []):
            for section in tab.get("sections", []):
                yield from section.get("folios", [])


def iterate_summary_entries(resource_report_config):
    yield from resource_report_config.get("header", {}).get("summary", [])
    for workspace in resource_report_config.get("workspaces", []):
        yield from workspace.get("config", {}).get("home", {}).get("summary", [])


def iterate_drawer_entries(resource_report_config, component):
    for workspace in resource_report_config.get("workspaces", []):
        drawer = workspace.get("config", {}).get("home", {}).get("drawer", [])
        for entry in drawer:
            if entry.get("component") == component:
                yield entry.get("config", {})


def iterate_related_graph_slugs(resource_report_config):
    for entry_config in iterate_drawer_entries(
        resource_report_config, RELATED_RESOURCES_PANEL
    ):
        yield from entry_config.get("graphs", [])


def validate_folio(report_graph, folio):
    nodegroup_alias = folio.get("nodegroup_alias")
    grouping_node = report_graph.grouping_nodes_by_alias.get(nodegroup_alias)
    if not grouping_node:
        raise ValidationError(
            f"Folio refers to an unknown nodegroup: {nodegroup_alias}"
        )
    if report_graph.parent_nodegroup_ids_by_nodegroup_id.get(
        grouping_node.nodegroup_id
    ):
        raise ValidationError(
            f"Folio {nodegroup_alias} is not a top-level nodegroup; its folio renders inside its parent's"
        )


def validate_resource_report_config(resource_report_config, graph):
    report_graph = ResourceReportGraph(graph)
    for folio in iterate_folios(resource_report_config):
        validate_folio(report_graph, folio)
    for summary_entry in iterate_summary_entries(resource_report_config):
        node_alias = summary_entry.get("node_alias")
        if node_alias not in report_graph.nodes_by_alias:
            raise ValidationError(f"Summary refers to an unknown node: {node_alias}")
    for graph_slug in iterate_related_graph_slugs(resource_report_config):
        if not GraphModel.objects.filter(slug=graph_slug, isresource=True).exists():
            raise ValidationError(
                f"Related resources panel refers to an unknown resource model: {graph_slug}"
            )


def prune_resource_report_config(
    resource_report_config, readable_nodegroup_ids, nodegroup_ids_by_node_alias
):
    def is_readable(node_alias):
        return nodegroup_ids_by_node_alias.get(node_alias) in readable_nodegroup_ids

    def prune_summary(summary_entries):
        return [
            summary_entry
            for summary_entry in summary_entries
            if is_readable(summary_entry.get("node_alias"))
        ]

    def prune_folios(folios):
        return [folio for folio in folios if is_readable(folio.get("nodegroup_alias"))]

    header = resource_report_config.get("header", {})
    if "summary" in header:
        header["summary"] = prune_summary(header["summary"])

    for workspace in resource_report_config.get("workspaces", []):
        workspace_config = workspace.get("config", {})
        if "tabs" in workspace_config:
            readable_tabs = []
            for tab in workspace_config["tabs"]:
                readable_sections = []
                for section in tab.get("sections", []):
                    section["folios"] = prune_folios(section.get("folios", []))
                    if section["folios"]:
                        readable_sections.append(section)
                tab["sections"] = readable_sections
                if readable_sections:
                    readable_tabs.append(tab)
            workspace_config["tabs"] = readable_tabs
        home = workspace_config.get("home", {})
        if "summary" in home:
            home["summary"] = prune_summary(home["summary"])

    return resource_report_config
