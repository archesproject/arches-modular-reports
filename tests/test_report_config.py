from django.core.exceptions import ValidationError
from django.test import TestCase

from arches.app.models.graph import Graph
from arches.app.models.models import CardModel, Node, NodeGroup

from arches_modular_reports.app.utils.resource_report_config import (
    RESOURCE_REPORT_COMPONENT,
)
from arches_modular_reports.app.utils.update_report_configuration_for_nodegroup_permissions import (
    update_report_configuration_with_nodegroup_permissions,
)
from arches_modular_reports.models import ReportConfig


def make_nodegroup(graph, alias, cardinality="n", parent_nodegroup=None):
    nodegroup = NodeGroup.objects.create(
        cardinality=cardinality, parentnodegroup=parent_nodegroup
    )
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


def make_card(graph, nodegroup, sortorder, visible=True):
    return CardModel.objects.create(
        graph=graph,
        nodegroup=nodegroup,
        name=nodegroup.grouping_node.name,
        sortorder=sortorder,
        visible=visible,
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
                    },
                    "views": [
                        {
                            "id": "report",
                            "component": "ReportView",
                            "label": {"en": "Report"},
                            "config": {
                                "tabs": [
                                    {
                                        "label": {"en": "Overview"},
                                        "sections": [
                                            {
                                                "cards": [
                                                    {
                                                        "nodegroup_alias": "production",
                                                        "component": "MapCard",
                                                        "row_fields": [
                                                            "name_content",
                                                            "type",
                                                        ],
                                                        "badge_field": "type",
                                                        "labels": {
                                                            "name_content": "Name"
                                                        },
                                                        "geometry_alias": "location_geometry",
                                                        "children": [
                                                            {
                                                                "nodegroup_alias": "production_location",
                                                                "component": "MultiValueCard",
                                                            }
                                                        ],
                                                    },
                                                    {
                                                        "nodegroup_alias": "identifiers",
                                                        "component": "MultiValueCard",
                                                    },
                                                ],
                                            }
                                        ],
                                    }
                                ],
                                "home": {
                                    "summary": [{"node_alias": "identifier_content"}],
                                },
                            },
                        },
                    ],
                },
            }
        ],
    }


def resource_report_config_from(config):
    return config["components"][0]["config"]


def first_card(config):
    return resource_report_config_from(config)["views"][0]["config"]["tabs"][0][
        "sections"
    ][0]["cards"][0]


class ResourceReportConfigTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.graph = Graph.objects.create_graph(is_resource=True, slug="test_graph")
        Graph.objects.filter(slug="test_graph").exclude(source_identifier=None).delete()

        cls.identifiers = make_nodegroup(cls.graph, "identifiers")
        make_node(cls.graph, cls.identifiers, "identifier_content", "string")
        make_card(cls.graph, cls.identifiers, sortorder=0)

        cls.production = make_nodegroup(cls.graph, "production")
        make_node(cls.graph, cls.production, "name_content", "string")
        make_node(cls.graph, cls.production, "type", "concept")
        make_card(cls.graph, cls.production, sortorder=1)

        cls.production_location = make_nodegroup(
            cls.graph, "production_location", parent_nodegroup=cls.production
        )
        make_node(
            cls.graph,
            cls.production_location,
            "location_geometry",
            "geojson-feature-collection",
        )
        make_card(cls.graph, cls.production_location, sortorder=0)

        cls.hidden = make_nodegroup(cls.graph, "hidden_branch")
        make_card(cls.graph, cls.hidden, sortorder=2, visible=False)

        cls.description = make_nodegroup(cls.graph, "description", cardinality="1")
        make_node(cls.graph, cls.description, "description_content", "string")
        make_card(cls.graph, cls.description, sortorder=3)

    def test_default_config_is_explicit_and_derived_from_the_graph(self):
        report_config = ReportConfig(graph=self.graph)
        report_config.full_clean()

        resource_report = report_config.config["components"][0]
        views = resource_report["config"]["views"]
        self.assertEqual(
            views[0]["config"]["tabs"][0]["sections"][0]["cards"],
            [
                {"nodegroup_alias": "identifiers", "component": "MultiValueCard"},
                {
                    "nodegroup_alias": "production",
                    "component": "NestedCard",
                    "children": [
                        {
                            "nodegroup_alias": "production_location",
                            "component": "MapCard",
                            "geometry_alias": "location_geometry",
                        }
                    ],
                },
                {"nodegroup_alias": "description", "component": "SimpleFieldCard"},
            ],
        )

    def test_curated_config_is_valid(self):
        ReportConfig(graph=self.graph, config=curated_config()).full_clean()

    def test_configs_that_contradict_the_graph_are_rejected(self):
        def mutate_unknown_nodegroup(config):
            first_card(config)["nodegroup_alias"] = "missing"

        def mutate_child_nodegroup_at_top_level(config):
            first_card(config)["nodegroup_alias"] = "production_location"
            del first_card(config)["children"]

        def mutate_child_under_the_wrong_parent(config):
            first_card(config)["children"][0]["nodegroup_alias"] = "identifiers"

        def mutate_row_field_outside_nodegroup(config):
            first_card(config)["row_fields"] = ["identifier_content"]

        def mutate_non_geometry_geometry_alias(config):
            first_card(config)["geometry_alias"] = "name_content"

        def mutate_unknown_summary_node(config):
            resource_report_config_from(config)["header"]["summary"] = [
                {"node_alias": "missing"}
            ]

        for mutation in (
            mutate_unknown_nodegroup,
            mutate_child_nodegroup_at_top_level,
            mutate_child_under_the_wrong_parent,
            mutate_row_field_outside_nodegroup,
            mutate_non_geometry_geometry_alias,
            mutate_unknown_summary_node,
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
        production_card = first_card(self.prune([self.production, self.identifiers]))
        self.assertEqual(production_card["nodegroup_alias"], "production")
        self.assertEqual(production_card["children"], [])

    def test_pruning_removes_unreadable_cards_summaries_and_empty_tabs(self):
        resource_report = resource_report_config_from(self.prune([self.identifiers]))
        self.assertEqual(resource_report["header"]["summary"], [])
        report_view_config = resource_report["views"][0]["config"]
        self.assertEqual(
            [
                card["nodegroup_alias"]
                for card in report_view_config["tabs"][0]["sections"][0]["cards"]
            ],
            ["identifiers"],
        )
        self.assertEqual(
            report_view_config["home"]["summary"],
            [{"node_alias": "identifier_content"}],
        )

        resource_report = resource_report_config_from(self.prune([]))
        self.assertEqual(resource_report["views"][0]["config"]["tabs"], [])
        self.assertEqual(resource_report["views"][0]["config"]["home"]["summary"], [])
