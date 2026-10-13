from pathlib import Path

from django.core.exceptions import ValidationError
from django.utils import translation
from django.utils.translation import gettext, gettext_noop

from arches.app.models.models import DDataType
from arches.app.models.system_settings import settings

RESOURCE_REPORT_COMPONENT = "arches_modular_reports/ResourceReport/ResourceReport"


def is_resource_report_component(component_path):
    return Path(component_path).stem == Path(RESOURCE_REPORT_COMPONENT).stem


def translated_labels(message):
    labels = {}
    for language in settings.LANGUAGES:
        with translation.override(language[0]):
            labels[language[0]] = gettext(message)
    return labels


class ResourceReportGraph:
    def __init__(self, graph):
        self.geometric_datatypes = set(
            DDataType.objects.filter(isgeometric=True).values_list(
                "datatype", flat=True
            )
        )
        graph_nodes = list(
            graph.node_set.select_related("nodegroup").prefetch_related(
                "cardxnodexwidget_set"
            )
        )
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
        self.nodes_by_nodegroup_id = {}
        for node in graph_nodes:
            if node.nodegroup_id:
                self.nodes_by_nodegroup_id.setdefault(node.nodegroup_id, []).append(
                    node
                )
        self.visible_cards = sorted(
            (card for card in graph.cardmodel_set.all() if card.visible),
            key=lambda card: card.sortorder or 0,
        )

    def child_nodegroup_ids(self, parent_nodegroup_id):
        return [
            card.nodegroup_id
            for card in self.visible_cards
            if self.parent_nodegroup_ids_by_nodegroup_id.get(card.nodegroup_id)
            == parent_nodegroup_id
        ]

    def visible_data_nodes(self, nodegroup_id):
        return [
            node
            for node in self.nodes_by_nodegroup_id.get(nodegroup_id, [])
            if node.datatype != "semantic"
            and all(widget.visible for widget in node.cardxnodexwidget_set.all())
        ]

    def is_descendant_nodegroup(self, nodegroup_id, ancestor_nodegroup_id):
        current_parent_id = self.parent_nodegroup_ids_by_nodegroup_id.get(nodegroup_id)
        while current_parent_id:
            if current_parent_id == ancestor_nodegroup_id:
                return True
            current_parent_id = self.parent_nodegroup_ids_by_nodegroup_id.get(
                current_parent_id
            )
        return False


def build_card_entry(report_graph, nodegroup_id):
    grouping_node = report_graph.grouping_nodes_by_nodegroup_id[nodegroup_id]
    child_nodegroup_ids = report_graph.child_nodegroup_ids(nodegroup_id)
    data_nodes = report_graph.visible_data_nodes(nodegroup_id)
    geometry_nodes = [
        node for node in data_nodes if node.datatype in report_graph.geometric_datatypes
    ]

    card_entry = {"nodegroup_alias": grouping_node.alias}
    if geometry_nodes:
        card_entry["component"] = "MapCard"
        card_entry["geometry_alias"] = geometry_nodes[0].alias
    elif child_nodegroup_ids:
        card_entry["component"] = "NestedCard"
    elif grouping_node.nodegroup.cardinality == "1" and len(data_nodes) == 1:
        card_entry["component"] = "SimpleFieldCard"
    else:
        card_entry["component"] = "MultiValueCard"
    if child_nodegroup_ids:
        card_entry["children"] = [
            build_card_entry(report_graph, child_nodegroup_id)
            for child_nodegroup_id in child_nodegroup_ids
        ]
    return card_entry


def view_entry(view_id, component, label, description):
    return {
        "id": view_id,
        "component": component,
        "label": translated_labels(label),
        "description": translated_labels(description),
    }


def drawer_entry(component, label, icon):
    return {"component": component, "label": translated_labels(label), "icon": icon}


def generate_resource_report_config(graph):
    report_graph = ResourceReportGraph(graph)
    report_view = {
        **view_entry(
            "report",
            "ReportView",
            gettext_noop("Report"),
            gettext_noop("A curated summary of this resource's data"),
        ),
        "config": {
            "tabs": [
                {
                    "label": translated_labels(gettext_noop("Overview")),
                    "sections": [
                        {
                            "cards": [
                                build_card_entry(report_graph, nodegroup_id)
                                for nodegroup_id in report_graph.child_nodegroup_ids(
                                    None
                                )
                            ]
                        }
                    ],
                }
            ],
            "home": {
                "summary": [],
                "drawer": [
                    drawer_entry(
                        "EditHistoryPanel", gettext_noop("Edit History"), "pi pi-clock"
                    ),
                    drawer_entry("ImagesPanel", gettext_noop("Images"), "pi pi-image"),
                    drawer_entry(
                        "RelatedResourcesPanel",
                        gettext_noop("Related Resources"),
                        "pi pi-link",
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
                        "summary": [],
                        "export_formats": ["json-ld", "json", "csv"],
                    },
                    "views": [
                        report_view,
                        view_entry(
                            "data",
                            "DataView",
                            gettext_noop("Data"),
                            gettext_noop(
                                "Browse and edit every field recorded on this resource"
                            ),
                        ),
                        view_entry(
                            "graph",
                            "GraphView",
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


def iterate_card_tree(cards, parent_card):
    for card in cards:
        yield card, parent_card
        yield from iterate_card_tree(card.get("children", []), parent_card=card)


def iterate_cards(resource_report_config):
    for view in resource_report_config.get("views", []):
        for tab in view.get("config", {}).get("tabs", []):
            for section in tab.get("sections", []):
                yield from iterate_card_tree(section.get("cards", []), None)


def iterate_summary_entries(resource_report_config):
    yield from resource_report_config.get("header", {}).get("summary", [])
    for view in resource_report_config.get("views", []):
        yield from view.get("config", {}).get("home", {}).get("summary", [])


def validate_card(report_graph, card, parent_card):
    nodegroup_alias = card.get("nodegroup_alias")
    grouping_node = report_graph.grouping_nodes_by_alias.get(nodegroup_alias)
    if not grouping_node:
        raise ValidationError(f"Card refers to an unknown nodegroup: {nodegroup_alias}")
    nodegroup_id = grouping_node.nodegroup_id

    if parent_card is None:
        if report_graph.parent_nodegroup_ids_by_nodegroup_id.get(nodegroup_id):
            raise ValidationError(
                f"Card {nodegroup_alias} is not a top-level nodegroup; nest it under its parent card's children"
            )
    else:
        parent_nodegroup_id = report_graph.grouping_nodes_by_alias[
            parent_card["nodegroup_alias"]
        ].nodegroup_id
        if not report_graph.is_descendant_nodegroup(nodegroup_id, parent_nodegroup_id):
            raise ValidationError(
                f"Card {nodegroup_alias} is not nested under its parent card's nodegroup"
            )

    nodegroup_node_aliases = {
        node.alias for node in report_graph.nodes_by_nodegroup_id[nodegroup_id]
    }
    referenced_node_aliases = [
        card.get("primary_field"),
        card.get("badge_field"),
        *card.get("row_fields", []),
        *card.get("labels", {}),
    ]
    for node_alias in referenced_node_aliases:
        if node_alias is not None and node_alias not in nodegroup_node_aliases:
            raise ValidationError(
                f"Card {nodegroup_alias} refers to a node outside its nodegroup: {node_alias}"
            )

    geometry_alias = card.get("geometry_alias")
    if geometry_alias is not None:
        geometry_node = report_graph.nodes_by_alias.get(geometry_alias)
        if (
            not geometry_node
            or geometry_node.datatype not in report_graph.geometric_datatypes
            or not (
                geometry_node.nodegroup_id == nodegroup_id
                or report_graph.is_descendant_nodegroup(
                    geometry_node.nodegroup_id, nodegroup_id
                )
            )
        ):
            raise ValidationError(
                f"Card {nodegroup_alias} geometry_alias is not a geometry node within this card: {geometry_alias}"
            )


def validate_resource_report_config(resource_report_config, graph):
    report_graph = ResourceReportGraph(graph)
    for card, parent_card in iterate_cards(resource_report_config):
        validate_card(report_graph, card, parent_card)
    for summary_entry in iterate_summary_entries(resource_report_config):
        node_alias = summary_entry.get("node_alias")
        if node_alias not in report_graph.nodes_by_alias:
            raise ValidationError(f"Summary refers to an unknown node: {node_alias}")


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

    def prune_cards(cards):
        readable_cards = []
        for card in cards:
            if not is_readable(card.get("nodegroup_alias")):
                continue
            if "children" in card:
                card["children"] = prune_cards(card["children"])
            readable_cards.append(card)
        return readable_cards

    header = resource_report_config.get("header", {})
    if "summary" in header:
        header["summary"] = prune_summary(header["summary"])

    for view in resource_report_config.get("views", []):
        view_config = view.get("config", {})
        if "tabs" in view_config:
            readable_tabs = []
            for tab in view_config["tabs"]:
                readable_sections = []
                for section in tab.get("sections", []):
                    section["cards"] = prune_cards(section.get("cards", []))
                    if section["cards"]:
                        readable_sections.append(section)
                tab["sections"] = readable_sections
                if readable_sections:
                    readable_tabs.append(tab)
            view_config["tabs"] = readable_tabs
        home = view_config.get("home", {})
        if "summary" in home:
            home["summary"] = prune_summary(home["summary"])

    return resource_report_config
