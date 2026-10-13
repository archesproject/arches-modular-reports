import copy

from django.core.exceptions import ValidationError
from django.test import TestCase

from arches.app.models.graph import Graph
from arches.app.models.models import CardModel, Node, NodeGroup

from arches_modular_reports.app.utils.update_report_configuration_for_nodegroup_permissions import (
    update_report_configuration_with_nodegroup_permissions,
)
from arches_modular_reports.models import ReportConfig
from arches_modular_reports.resource_report import RESOURCE_REPORT_COMPONENT


def make_nodegroup(graph, alias, parent_nodegroup=None):
    nodegroup = NodeGroup.objects.create(parentnodegroup=parent_nodegroup)
    grouping_node = Node.objects.create(
        pk=nodegroup.pk,
        name=alias.replace("_", " ").title(),
        alias=alias,
        graph=graph,
        nodegroup=nodegroup,
        datatype="semantic",
        istopnode=False,
    )
    nodegroup.grouping_node = grouping_node
    nodegroup.save()
    return nodegroup


def make_node(graph, nodegroup, alias, datatype):
    return Node.objects.create(
        nodegroup=nodegroup,
        name=alias.replace("_", " ").title(),
        alias=alias,
        graph=graph,
        istopnode=False,
        datatype=datatype,
    )


def curated_config():
    return {
        "name": "Curated",
        "components": [
            {
                "component": RESOURCE_REPORT_COMPONENT,
                "config": {
                    "header": {
                        "summary": [{"node_alias": "name_content", "label": "Name"}],
                        "export_formats": ["json-ld", "csv"],
                        "lifecycle_severities": {"any-state-id": "warn"},
                    },
                    "views": [
                        {
                            "id": "report",
                            "label": {"en": "Report", "es": "Informe"},
                            "component": "ReportView",
                            "config": {
                                "tabs": [
                                    {
                                        "label": "Overview",
                                        "sections": [
                                            {
                                                "label": "Production",
                                                "icon": "pi pi-box",
                                                "cards": [
                                                    {
                                                        "nodegroup_alias": "production",
                                                        "display": "accordion",
                                                        "page_size": 5,
                                                        "row_fields": [
                                                            "name_content",
                                                            "type",
                                                        ],
                                                        "badge_field": "type",
                                                        "hide_row_field_labels": True,
                                                        "labels": {
                                                            "name_content": "Name"
                                                        },
                                                        "geometry_alias": "location_geometry",
                                                        "children": [
                                                            {
                                                                "nodegroup_alias": "production_location",
                                                                "display": "table",
                                                            }
                                                        ],
                                                    },
                                                    {
                                                        "nodegroup_alias": "identifiers",
                                                        "component": "SimpleFieldCard",
                                                    },
                                                ],
                                            }
                                        ],
                                    }
                                ],
                                "home": {
                                    "summary": [{"node_alias": "identifier_content"}],
                                    "drawer": [
                                        "edit_history",
                                        {
                                            "component": "my_app/Report/CustomPanel",
                                            "label": "Custom",
                                            "icon": "pi pi-star",
                                        },
                                    ],
                                },
                            },
                        },
                        {"id": "data", "component": "DataView"},
                        {"id": "custom", "component": "my_app/Report/CustomView"},
                    ],
                },
            }
        ],
    }


class ResourceReportConfigTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.graph = Graph.objects.create_graph(is_resource=True, slug="test_graph")
        Graph.objects.filter(slug="test_graph").exclude(source_identifier=None).delete()

        cls.production = make_nodegroup(cls.graph, "production")
        make_node(cls.graph, cls.production, "name_content", "string")
        make_node(cls.graph, cls.production, "type", "concept")
        CardModel.objects.create(
            graph=cls.graph,
            nodegroup=cls.production,
            name="Production",
            sortorder=1,
            visible=True,
        )

        cls.production_location = make_nodegroup(
            cls.graph, "production_location", parent_nodegroup=cls.production
        )
        make_node(
            cls.graph,
            cls.production_location,
            "location_geometry",
            "geojson-feature-collection",
        )
        make_node(cls.graph, cls.production_location, "location_note", "string")
        CardModel.objects.create(
            graph=cls.graph,
            nodegroup=cls.production_location,
            name="Production Location",
            sortorder=0,
            visible=True,
        )

        cls.identifiers = make_nodegroup(cls.graph, "identifiers")
        make_node(cls.graph, cls.identifiers, "identifier_content", "string")
        CardModel.objects.create(
            graph=cls.graph,
            nodegroup=cls.identifiers,
            name="Identifiers",
            sortorder=0,
            visible=True,
        )

        cls.hidden = make_nodegroup(cls.graph, "hidden_branch")
        CardModel.objects.create(
            graph=cls.graph,
            nodegroup=cls.hidden,
            name="Hidden",
            sortorder=2,
            visible=False,
        )

    def test_default_config_lists_visible_top_level_cards_in_card_order(self):
        report_config = ReportConfig(graph=self.graph)
        report_config.full_clean()

        resource_report = report_config.config["components"][0]
        self.assertEqual(resource_report["component"], RESOURCE_REPORT_COMPONENT)
        report_view = resource_report["config"]["views"][0]
        self.assertEqual(
            report_view["config"]["tabs"][0]["sections"][0]["cards"],
            [{"nodegroup_alias": "identifiers"}, {"nodegroup_alias": "production"}],
        )
        self.assertEqual(
            [view["component"] for view in resource_report["config"]["views"]],
            ["ReportView", "DataView", "GraphView"],
        )

    def test_curated_config_is_valid(self):
        ReportConfig(graph=self.graph, config=curated_config()).full_clean()

    def test_custom_card_component_options_are_not_validated(self):
        config = curated_config()
        cards = self.resource_report_config_from(config)["views"][0]["config"]["tabs"][
            0
        ]["sections"][0]["cards"]
        cards.append(
            {
                "nodegroup_alias": "identifiers",
                "component": "my_app/Report/CustomCard",
                "anything": {"goes": True},
            }
        )
        ReportConfig(graph=self.graph, config=config).full_clean()

    def resource_report_config_from(self, config):
        return config["components"][0]["config"]

    def test_invalid_configs_are_rejected(self):
        def first_card(config):
            return self.resource_report_config_from(config)["views"][0]["config"][
                "tabs"
            ][0]["sections"][0]["cards"][0]

        def mutate_unknown_top_level_key(config):
            self.resource_report_config_from(config)["bogus"] = True

        def mutate_duplicate_view_id(config):
            self.resource_report_config_from(config)["views"][1]["id"] = "report"

        def mutate_unknown_view_component(config):
            self.resource_report_config_from(config)["views"][1]["component"] = "Nope"

        def mutate_data_view_config(config):
            self.resource_report_config_from(config)["views"][1]["config"] = {"x": 1}

        def mutate_unknown_nodegroup(config):
            first_card(config)["nodegroup_alias"] = "missing"

        def mutate_child_nodegroup_at_top_level(config):
            first_card(config)["nodegroup_alias"] = "production_location"
            del first_card(config)["children"]

        def mutate_row_field_outside_nodegroup(config):
            first_card(config)["row_fields"] = ["identifier_content"]

        def mutate_non_geometry_geometry_alias(config):
            first_card(config)["geometry_alias"] = "name_content"

        def mutate_unknown_display_mode(config):
            first_card(config)["display"] = "carousel"

        def mutate_non_positive_page_size(config):
            first_card(config)["page_size"] = 0

        def mutate_unknown_card_key(config):
            first_card(config)["colour"] = "blue"

        def mutate_unknown_drawer_panel(config):
            self.resource_report_config_from(config)["views"][0]["config"]["home"][
                "drawer"
            ].append("workflows")

        def mutate_unknown_export_format(config):
            self.resource_report_config_from(config)["header"]["export_formats"] = [
                "xml"
            ]

        def mutate_unknown_lifecycle_severity(config):
            self.resource_report_config_from(config)["header"][
                "lifecycle_severities"
            ] = {"any-state-id": "purple"}

        def mutate_invalid_label(config):
            first_card(config)["label"] = ["not", "a", "label"]

        def mutate_semantic_summary_node(config):
            self.resource_report_config_from(config)["header"]["summary"] = [
                {"node_alias": "production"}
            ]

        for mutation in (
            mutate_unknown_top_level_key,
            mutate_duplicate_view_id,
            mutate_unknown_view_component,
            mutate_data_view_config,
            mutate_unknown_nodegroup,
            mutate_child_nodegroup_at_top_level,
            mutate_row_field_outside_nodegroup,
            mutate_non_geometry_geometry_alias,
            mutate_unknown_display_mode,
            mutate_non_positive_page_size,
            mutate_unknown_card_key,
            mutate_unknown_drawer_panel,
            mutate_unknown_export_format,
            mutate_invalid_label,
            mutate_unknown_lifecycle_severity,
            mutate_semantic_summary_node,
        ):
            with self.subTest(mutation=mutation.__name__):
                config = curated_config()
                mutation(config)
                with self.assertRaises(ValidationError):
                    ReportConfig(graph=self.graph, config=config).full_clean()

    def prune(self, readable_nodegroups):
        report_config = ReportConfig(graph=self.graph, config=curated_config())
        return update_report_configuration_with_nodegroup_permissions(
            report_configuration_instance=report_config,
            report_nodegroup_ids_with_user_read_permission={
                nodegroup.pk for nodegroup in readable_nodegroups
            },
            report_nodegroup_ids_with_user_write_permission=set(),
        )

    def test_pruning_removes_unreadable_child_cards(self):
        pruned = self.prune([self.production, self.identifiers])
        production_card = self.resource_report_config_from(pruned)["views"][0][
            "config"
        ]["tabs"][0]["sections"][0]["cards"][0]
        self.assertEqual(production_card["nodegroup_alias"], "production")
        self.assertEqual(production_card["children"], [])

    def test_pruning_removes_unreadable_cards_summaries_and_empty_tabs(self):
        pruned = self.prune([self.identifiers])
        resource_report = self.resource_report_config_from(pruned)
        self.assertEqual(resource_report["header"]["summary"], [])
        cards = resource_report["views"][0]["config"]["tabs"][0]["sections"][0]["cards"]
        self.assertEqual(
            [card["nodegroup_alias"] for card in cards],
            ["identifiers"],
        )
        self.assertEqual(
            resource_report["views"][0]["config"]["home"]["summary"],
            [{"node_alias": "identifier_content"}],
        )

        pruned = self.prune([])
        resource_report = self.resource_report_config_from(pruned)
        self.assertEqual(resource_report["views"][0]["config"]["tabs"], [])
        self.assertEqual(resource_report["views"][0]["config"]["home"]["summary"], [])

    def test_pruning_leaves_stored_config_untouched(self):
        report_config = ReportConfig(graph=self.graph, config=curated_config())
        original_config = copy.deepcopy(report_config.config)
        update_report_configuration_with_nodegroup_permissions(
            report_configuration_instance=report_config,
            report_nodegroup_ids_with_user_read_permission=set(),
            report_nodegroup_ids_with_user_write_permission=set(),
        )
        self.assertEqual(report_config.config, original_config)
