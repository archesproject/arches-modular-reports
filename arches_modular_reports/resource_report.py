from pathlib import Path

from django.core.exceptions import ValidationError

RESOURCE_REPORT_COMPONENT = "arches_modular_reports/ResourceReport/ResourceReport"

BUILT_IN_VIEW_COMPONENTS = {"ReportView", "DataView", "GraphView"}
BUILT_IN_CARD_COMPONENTS = {
    "SimpleFieldCard",
    "MultiValueCard",
    "NestedCard",
    "MapCard",
    "DefaultCard",
}
BUILT_IN_DRAWER_PANELS = {"edit_history", "images", "related_resources", "manage"}
DEFAULT_DRAWER_PANELS = ["edit_history", "images", "related_resources", "manage"]
DISPLAY_MODES = {"cards", "accordion", "table"}
EXPORT_FORMATS = {"json-ld", "json", "csv"}
LIFECYCLE_SEVERITIES = {"info", "success", "warn", "danger", "secondary", "contrast"}
GEOMETRY_DATATYPE = "geojson-feature-collection"

CONFIG_KEYS = {"header", "views"}
HEADER_KEYS = {"summary", "export_formats", "lifecycle_severities"}
SUMMARY_ENTRY_KEYS = {"node_alias", "label"}
VIEW_KEYS = {"id", "label", "description", "component", "config"}
REPORT_VIEW_CONFIG_KEYS = {"tabs", "home"}
TAB_KEYS = {"label", "sections"}
SECTION_KEYS = {"label", "icon", "cards"}
HOME_KEYS = {"summary", "drawer"}
DRAWER_ENTRY_KEYS = {"component", "label", "icon", "config"}
CARD_KEYS = {
    "nodegroup_alias",
    "component",
    "label",
    "labels",
    "display",
    "page_size",
    "primary_field",
    "row_fields",
    "hide_row_field_labels",
    "single_line_fields",
    "badge_field",
    "geometry_alias",
    "children",
}
CARD_BOOLEAN_KEYS = {"hide_row_field_labels", "single_line_fields"}


def is_resource_report_component(component_path):
    return Path(component_path).stem == Path(RESOURCE_REPORT_COMPONENT).stem


def is_import_path(component_name):
    return "/" in component_name


def generate_resource_report_config(graph):
    top_level_cards = (
        graph.cardmodel_set.filter(
            nodegroup__parentnodegroup__isnull=True,
            visible=True,
        )
        .select_related("nodegroup__grouping_node")
        .order_by("sortorder")
    )
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
                        {
                            "id": "report",
                            "component": "ReportView",
                            "config": {
                                "tabs": [
                                    {
                                        "sections": [
                                            {
                                                "cards": [
                                                    {
                                                        "nodegroup_alias": card.nodegroup.grouping_node.alias
                                                    }
                                                    for card in top_level_cards
                                                ]
                                            }
                                        ]
                                    }
                                ],
                                "home": {
                                    "summary": [],
                                    "drawer": list(DEFAULT_DRAWER_PANELS),
                                },
                            },
                        },
                        {"id": "data", "component": "DataView"},
                        {"id": "graph", "component": "GraphView"},
                    ],
                },
            }
        ],
    }


class ResourceReportConfigValidator:
    def __init__(self, graph):
        graph_nodes = list(graph.node_set.select_related("nodegroup"))
        self.nodes_by_alias = {node.alias: node for node in graph_nodes if node.alias}
        self.grouping_nodes_by_alias = {
            node.alias: node
            for node in graph_nodes
            if node.alias and node.nodegroup_id == node.pk
        }
        self.parent_nodegroup_ids_by_nodegroup_id = {
            node.nodegroup_id: node.nodegroup.parentnodegroup_id
            for node in graph_nodes
            if node.nodegroup_id
        }

    def validate(self, config):
        self.require_dict(config, "ResourceReport config")
        self.reject_unknown_keys(config, CONFIG_KEYS, "ResourceReport config")
        if "header" in config:
            self.validate_header(config["header"])
        if "views" in config:
            self.validate_views(config["views"])

    def validate_header(self, header):
        self.require_dict(header, "Header")
        self.reject_unknown_keys(header, HEADER_KEYS, "Header")
        if "summary" in header:
            self.validate_summary(header["summary"], "Header")
        if "export_formats" in header:
            export_formats = header["export_formats"]
            self.require_list(export_formats, "Header export_formats")
            if unknown_formats := set(export_formats) - EXPORT_FORMATS:
                raise ValidationError(
                    f"Header contains unknown export formats: {unknown_formats}"
                )
        if "lifecycle_severities" in header:
            lifecycle_severities = header["lifecycle_severities"]
            self.require_dict(lifecycle_severities, "Header lifecycle_severities")
            if unknown_severities := (
                set(lifecycle_severities.values()) - LIFECYCLE_SEVERITIES
            ):
                raise ValidationError(
                    f"Header contains unknown lifecycle severities: {unknown_severities}"
                )

    def validate_summary(self, summary_entries, section_name):
        self.require_list(summary_entries, f"{section_name} summary")
        for summary_entry in summary_entries:
            self.require_dict(summary_entry, f"{section_name} summary entry")
            self.reject_unknown_keys(
                summary_entry, SUMMARY_ENTRY_KEYS, f"{section_name} summary entry"
            )
            node_alias = self.require_string(
                summary_entry, "node_alias", f"{section_name} summary entry"
            )
            summarized_node = self.nodes_by_alias.get(node_alias)
            if not summarized_node or summarized_node.datatype == "semantic":
                raise ValidationError(
                    f"{section_name} summary refers to an invalid node alias: {node_alias}"
                )
            self.validate_label(summary_entry.get("label"), f"{section_name} summary")

    def validate_views(self, views):
        self.require_list(views, "Views")
        seen_view_ids = set()
        for view in views:
            self.require_dict(view, "View")
            self.reject_unknown_keys(view, VIEW_KEYS, "View")
            view_id = self.require_string(view, "id", "View")
            if view_id in seen_view_ids:
                raise ValidationError(f"Duplicate view id: {view_id}")
            seen_view_ids.add(view_id)
            component = self.require_string(view, "component", f"View {view_id}")
            self.validate_label(view.get("label"), f"View {view_id}")
            self.validate_label(view.get("description"), f"View {view_id}")
            view_config = view.get("config", {})
            self.require_dict(view_config, f"View {view_id} config")
            if component == "ReportView":
                self.validate_report_view_config(view_config)
            elif component in BUILT_IN_VIEW_COMPONENTS:
                if view_config:
                    raise ValidationError(f"View {view_id} does not accept config")
            elif not is_import_path(component):
                raise ValidationError(f"Unknown view component: {component}")

    def validate_report_view_config(self, report_view_config):
        self.reject_unknown_keys(
            report_view_config, REPORT_VIEW_CONFIG_KEYS, "Report view config"
        )
        if "tabs" in report_view_config:
            self.validate_tabs(report_view_config["tabs"])
        if "home" in report_view_config:
            self.validate_home(report_view_config["home"])

    def validate_tabs(self, tabs):
        self.require_list(tabs, "Tabs")
        for tab in tabs:
            self.require_dict(tab, "Tab")
            self.reject_unknown_keys(tab, TAB_KEYS, "Tab")
            self.validate_label(tab.get("label"), "Tab")
            sections = tab.get("sections", [])
            self.require_list(sections, "Tab sections")
            for section in sections:
                self.require_dict(section, "Section")
                self.reject_unknown_keys(section, SECTION_KEYS, "Section")
                self.validate_label(section.get("label"), "Section")
                if "icon" in section:
                    self.require_string(section, "icon", "Section")
                cards = section.get("cards", [])
                self.require_list(cards, "Section cards")
                for card in cards:
                    self.validate_card(card, parent_nodegroup_id=None)

    def validate_home(self, home):
        self.require_dict(home, "Home")
        self.reject_unknown_keys(home, HOME_KEYS, "Home")
        if "summary" in home:
            self.validate_summary(home["summary"], "Home")
        if "drawer" in home:
            drawer_entries = home["drawer"]
            self.require_list(drawer_entries, "Home drawer")
            for drawer_entry in drawer_entries:
                if isinstance(drawer_entry, str):
                    if drawer_entry not in BUILT_IN_DRAWER_PANELS:
                        raise ValidationError(f"Unknown drawer panel: {drawer_entry}")
                    continue
                self.require_dict(drawer_entry, "Drawer entry")
                self.reject_unknown_keys(
                    drawer_entry, DRAWER_ENTRY_KEYS, "Drawer entry"
                )
                component = self.require_string(
                    drawer_entry, "component", "Drawer entry"
                )
                if component not in BUILT_IN_DRAWER_PANELS and not is_import_path(
                    component
                ):
                    raise ValidationError(f"Unknown drawer panel: {component}")
                self.validate_label(drawer_entry.get("label"), "Drawer entry")

    def validate_card(self, card, parent_nodegroup_id):
        self.require_dict(card, "Card")
        nodegroup_alias = self.require_string(card, "nodegroup_alias", "Card")
        section_name = f"Card {nodegroup_alias}"
        grouping_node = self.grouping_nodes_by_alias.get(nodegroup_alias)
        if not grouping_node:
            raise ValidationError(
                f"Card refers to an unknown nodegroup: {nodegroup_alias}"
            )
        card_nodegroup_id = grouping_node.nodegroup_id
        if parent_nodegroup_id is None:
            if self.parent_nodegroup_ids_by_nodegroup_id.get(card_nodegroup_id):
                raise ValidationError(
                    f"{section_name} is not a top-level nodegroup; nest it under its parent card's children"
                )
        elif not self.is_descendant_nodegroup(card_nodegroup_id, parent_nodegroup_id):
            raise ValidationError(
                f"{section_name} is not nested under its parent card's nodegroup"
            )

        component = card.get("component")
        if component is not None:
            self.require_string(card, "component", section_name)
            if component not in BUILT_IN_CARD_COMPONENTS:
                if not is_import_path(component):
                    raise ValidationError(f"Unknown card component: {component}")
                return
        self.reject_unknown_keys(card, CARD_KEYS, section_name)

        nodegroup_node_aliases = {
            node.alias
            for node in self.nodes_by_alias.values()
            if node.nodegroup_id == card_nodegroup_id and node.datatype != "semantic"
        }

        self.validate_label(card.get("label"), section_name)
        if "labels" in card:
            self.require_dict(card["labels"], f"{section_name} labels")
            for node_alias, node_label in card["labels"].items():
                self.require_node_alias_in(
                    node_alias, nodegroup_node_aliases, section_name
                )
                self.validate_label(node_label, section_name)
        if "display" in card and card["display"] not in DISPLAY_MODES:
            raise ValidationError(
                f"{section_name} has an unknown display mode: {card['display']}"
            )
        if "page_size" in card:
            page_size = card["page_size"]
            if not isinstance(page_size, int) or isinstance(page_size, bool):
                raise ValidationError(f"{section_name} page_size is not an integer")
            if page_size < 1:
                raise ValidationError(f"{section_name} page_size must be positive")
        for boolean_key in CARD_BOOLEAN_KEYS:
            if boolean_key in card and not isinstance(card[boolean_key], bool):
                raise ValidationError(f"{section_name} {boolean_key} is not a boolean")
        for single_alias_key in ("primary_field", "badge_field"):
            if single_alias_key in card:
                self.require_node_alias_in(
                    card[single_alias_key], nodegroup_node_aliases, section_name
                )
        if "row_fields" in card:
            self.require_list(card["row_fields"], f"{section_name} row_fields")
            for node_alias in card["row_fields"]:
                self.require_node_alias_in(
                    node_alias, nodegroup_node_aliases, section_name
                )
        if "geometry_alias" in card:
            geometry_node = self.nodes_by_alias.get(card["geometry_alias"])
            if (
                not geometry_node
                or geometry_node.datatype != GEOMETRY_DATATYPE
                or not (
                    geometry_node.nodegroup_id == card_nodegroup_id
                    or self.is_descendant_nodegroup(
                        geometry_node.nodegroup_id, card_nodegroup_id
                    )
                )
            ):
                raise ValidationError(
                    f"{section_name} geometry_alias is not a geometry node within this card: {card['geometry_alias']}"
                )
        if "children" in card:
            self.require_list(card["children"], f"{section_name} children")
            for child_card in card["children"]:
                self.validate_card(child_card, parent_nodegroup_id=card_nodegroup_id)

    def is_descendant_nodegroup(self, nodegroup_id, ancestor_nodegroup_id):
        current_parent_id = self.parent_nodegroup_ids_by_nodegroup_id.get(nodegroup_id)
        while current_parent_id:
            if current_parent_id == ancestor_nodegroup_id:
                return True
            current_parent_id = self.parent_nodegroup_ids_by_nodegroup_id.get(
                current_parent_id
            )
        return False

    @staticmethod
    def require_node_alias_in(node_alias, allowed_node_aliases, section_name):
        if node_alias not in allowed_node_aliases:
            raise ValidationError(
                f"{section_name} refers to a node alias outside its nodegroup: {node_alias}"
            )

    @staticmethod
    def validate_label(label, section_name):
        if label is None or isinstance(label, str):
            return
        if isinstance(label, dict) and all(
            isinstance(language_code, str) and isinstance(localized_label, str)
            for language_code, localized_label in label.items()
        ):
            return
        raise ValidationError(
            f"{section_name} label must be a string or a mapping of language codes to strings"
        )

    @staticmethod
    def reject_unknown_keys(config_dict, allowed_keys, section_name):
        if unknown_keys := set(config_dict) - allowed_keys:
            raise ValidationError(
                f"{section_name} contains unknown keys: {unknown_keys}"
            )

    @staticmethod
    def require_dict(value, section_name):
        if not isinstance(value, dict):
            raise ValidationError(f"{section_name} is not an object")

    @staticmethod
    def require_list(value, section_name):
        if not isinstance(value, list):
            raise ValidationError(f"{section_name} is not a list")

    @staticmethod
    def require_string(config_dict, key, section_name):
        if key not in config_dict:
            raise ValidationError(f"{section_name} missing key: {key}")
        value = config_dict[key]
        if not isinstance(value, str):
            raise ValidationError(f"{section_name} {key} is not a string")
        return value


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
        if view.get("component") != "ReportView":
            continue
        report_view_config = view.get("config", {})
        if "tabs" in report_view_config:
            readable_tabs = []
            for tab in report_view_config["tabs"]:
                readable_sections = []
                for section in tab.get("sections", []):
                    section["cards"] = prune_cards(section.get("cards", []))
                    if section["cards"]:
                        readable_sections.append(section)
                tab["sections"] = readable_sections
                if readable_sections:
                    readable_tabs.append(tab)
            report_view_config["tabs"] = readable_tabs
        home = report_view_config.get("home", {})
        if "summary" in home:
            home["summary"] = prune_summary(home["summary"])

    return resource_report_config
