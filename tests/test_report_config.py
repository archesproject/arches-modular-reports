from django.core.exceptions import ValidationError
from django.test import TestCase

from arches.app.models.graph import Graph
from arches.app.models.models import (
    CardModel,
    Function,
    FunctionXGraph,
    Node,
    NodeGroup,
)

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
                    "workspaces": [
                        {
                            "id": "report",
                            "component": "ReportWorkspace",
                            "label": {"en": "Report"},
                            "config": {
                                "tabs": [
                                    {
                                        "label": {"en": "Overview"},
                                        "sections": [
                                            {
                                                "folios": [
                                                    {"nodegroup_alias": "production"},
                                                    {"nodegroup_alias": "identifiers"},
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


def generated_folio(nodegroup_alias):
    return {"nodegroup_alias": nodegroup_alias}


def resource_report_config_from(config):
    return config["components"][0]["config"]


def first_folio(config):
    return resource_report_config_from(config)["workspaces"][0]["config"]["tabs"][0][
        "sections"
    ][0]["folios"][0]


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

        FunctionXGraph.objects.create(
            graph=cls.graph,
            function=Function.objects.filter(functiontype="primarydescriptors").first(),
            config={
                "descriptor_types": {
                    "name": {"string_template": "<name_content> #<identifier_content>"},
                    "description": {
                        "nodegroup_id": str(cls.description.pk),
                        "string_template": "<Description Content>",
                    },
                    "map_popup": {"string_template": "<retired_alias>"},
                }
            },
        )

    def test_default_config_is_explicit_and_derived_from_the_graph(self):
        report_config = ReportConfig(graph=self.graph)
        report_config.full_clean()

        resource_report = report_config.config["components"][0]
        self.assertEqual(
            resource_report["config"]["header"]["summary"],
            [{"node_alias": "description_content", "label": None}],
        )
        workspaces = resource_report["config"]["workspaces"]
        self.assertEqual(
            workspaces[0]["config"]["home"]["summary"],
            [
                {"node_alias": "name_content", "label": None},
                {"node_alias": "identifier_content", "label": None},
                {"node_alias": "description_content", "label": None},
            ],
        )
        self.assertEqual(
            workspaces[0]["config"]["tabs"][0]["sections"][0]["folios"],
            [
                generated_folio("identifiers"),
                generated_folio("production"),
                generated_folio("description"),
            ],
        )

    def test_curated_config_is_valid(self):
        ReportConfig(graph=self.graph, config=curated_config()).full_clean()

    def test_configs_that_contradict_the_graph_are_rejected(self):
        def mutate_unknown_nodegroup(config):
            first_folio(config)["nodegroup_alias"] = "missing"

        def mutate_child_nodegroup_at_top_level(config):
            first_folio(config)["nodegroup_alias"] = "production_location"

        def mutate_unknown_summary_node(config):
            resource_report_config_from(config)["header"]["summary"] = [
                {"node_alias": "missing"}
            ]

        for mutation in (
            mutate_unknown_nodegroup,
            mutate_child_nodegroup_at_top_level,
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

    def test_pruning_removes_unreadable_folios_summaries_and_empty_tabs(self):
        resource_report = resource_report_config_from(self.prune([self.identifiers]))
        self.assertEqual(resource_report["header"]["summary"], [])
        report_workspace_config = resource_report["workspaces"][0]["config"]
        self.assertEqual(
            [
                folio["nodegroup_alias"]
                for folio in report_workspace_config["tabs"][0]["sections"][0]["folios"]
            ],
            ["identifiers"],
        )
        self.assertEqual(
            report_workspace_config["home"]["summary"],
            [{"node_alias": "identifier_content"}],
        )

        resource_report = resource_report_config_from(self.prune([]))
        self.assertEqual(resource_report["workspaces"][0]["config"]["tabs"], [])
        self.assertEqual(
            resource_report["workspaces"][0]["config"]["home"]["summary"], []
        )
