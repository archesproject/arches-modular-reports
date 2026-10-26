from django.core.exceptions import ValidationError
from django.test import TestCase

from arches.app.models.graph import Graph
from arches.app.models.models import (
    CardModel,
    CardXNodeXWidget,
    Function,
    FunctionXGraph,
    GraphModel,
    Node,
    NodeGroup,
    Widget,
)

from arches_modular_reports.app.utils.resource_report_config import (
    REPORT_COMPONENTS_PATH,
    RESOURCE_REPORT_COMPONENT,
    report_component,
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


def make_resource_model(slug, name):
    Graph.objects.create_graph(is_resource=True, slug=slug)
    Graph.objects.filter(slug=slug).exclude(source_identifier=None).delete()
    GraphModel.objects.filter(slug=slug).update(name={"en": name})
    return GraphModel.objects.get(slug=slug)


def curated_config():
    return {
        "name": "Curated",
        "components": [
            {
                "component": RESOURCE_REPORT_COMPONENT,
                "config": {
                    "components": [
                        report_component(
                            "ReportHeader",
                            {
                                "summary": [
                                    {"node_alias": "name_content", "label": "Name"}
                                ],
                            },
                        ),
                        report_component(
                            "SplitPane",
                            {
                                "main": [
                                    report_component(
                                        "ReportSection",
                                        {
                                            "label": {"en": "Production"},
                                            "icon": "pi pi-cog",
                                            "components": [
                                                report_component(
                                                    "ReportFolio",
                                                    {"nodegroup_alias": "production"},
                                                )
                                            ],
                                        },
                                    ),
                                    report_component(
                                        "ReportSection",
                                        {
                                            "label": {"en": "Identifiers"},
                                            "icon": None,
                                            "components": [
                                                report_component(
                                                    "ReportFolio",
                                                    {"nodegroup_alias": "identifiers"},
                                                )
                                            ],
                                        },
                                    ),
                                ],
                                "aside": [
                                    report_component(
                                        "KeyDataSummary",
                                        {
                                            "summary": [
                                                {
                                                    "node_alias": "identifier_content",
                                                    "label": "Identifier",
                                                }
                                            ]
                                        },
                                    )
                                ],
                            },
                        ),
                    ]
                },
            }
        ],
    }


def data_section(nodegroup_alias, node_aliases, **extra_config):
    return {
        "component": "arches_modular_reports/ModularReport/components/DataSection",
        "config": {
            "nodegroup_alias": nodegroup_alias,
            "node_aliases": node_aliases,
            **extra_config,
        },
    }


def legacy_config(*components):
    return {"name": "Legacy", "components": list(components)}


def component_path(component_name):
    return f"{REPORT_COMPONENTS_PATH}/{component_name}"


def find_components(value, component_name):
    found = []
    if isinstance(value, list):
        for item in value:
            found.extend(find_components(item, component_name))
    elif isinstance(value, dict):
        if value.get("component") == component_path(component_name):
            found.append(value)
        for child_value in value.values():
            found.extend(find_components(child_value, component_name))
    return found


def resource_report_config_from(config):
    return config["components"][0]["config"]


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
                    "name": {
                        "nodegroup_id": str(cls.production.pk),
                        "string_template": "<Name Content>",
                    },
                    "description": {
                        "nodegroup_id": str(cls.description.pk),
                        "string_template": "<Description Content>",
                    },
                    "map_popup": {
                        "nodegroup_id": str(cls.identifiers.pk),
                        "string_template": "#<Identifier Content> <Retired Node>",
                    },
                }
            },
        )

    def test_default_config_is_explicit_and_derived_from_the_graph(self):
        report_config = ReportConfig(graph=self.graph)
        report_config.full_clean()

        config = report_config.config
        self.assertEqual(
            [
                child["component"]
                for child in resource_report_config_from(config)["components"]
            ],
            [
                component_path("WorkspaceTabs"),
                component_path("EditListTray"),
            ],
        )
        workspace_tabs = find_components(config, "WorkspaceTabs")[0]["config"]
        self.assertEqual(
            [banner_node["component"] for banner_node in workspace_tabs["banner"]],
            [component_path("ReportHeader")],
        )
        self.assertEqual(
            [
                (workspace["component"], workspace["config"].get("requires_edit"))
                for workspace in workspace_tabs["components"]
            ],
            [
                (component_path("SplitPane"), None),
                (component_path("SplitPane"), True),
                (component_path("ReportPlaceholder"), None),
            ],
        )
        self.assertEqual(
            find_components(config, "ReportHeader")[0]["config"]["summary"],
            [{"node_alias": "description_content", "label": "Description Content"}],
        )
        self.assertEqual(
            find_components(config, "KeyDataSummary")[0]["config"]["summary"],
            [
                {"node_alias": "name_content", "label": "Name Content"},
                {"node_alias": "description_content", "label": "Description Content"},
                {"node_alias": "identifier_content", "label": "Identifier Content"},
            ],
        )
        overview = find_components(config, "ReportStack")[0]
        self.assertEqual(
            [
                (folio["component"], folio["config"]["nodegroup_alias"])
                for folio in overview["config"]["components"]
            ],
            [
                (component_path("ReportFolio"), "identifiers"),
                (component_path("ReportFolio"), "production"),
                (component_path("FieldFolio"), "description"),
            ],
        )

    def test_nodegroups_with_geometry_get_a_map_folio(self):
        site = make_nodegroup(self.graph, "site")
        make_node(self.graph, site, "site_name", "string")
        make_node(self.graph, site, "site_geometry", "geojson-feature-collection")
        make_card(self.graph, site, sortorder=4)

        report_config = ReportConfig(graph=self.graph)
        report_config.full_clean()

        self.assertEqual(
            find_components(report_config.config, "MapFolio")[0]["config"],
            {"nodegroup_alias": "site", "node_alias": "site_geometry"},
        )

    def test_summary_labels_come_from_widgets(self):
        CardXNodeXWidget.objects.create(
            card=CardModel.objects.get(nodegroup=self.production),
            node=Node.objects.get(graph=self.graph, alias="name_content"),
            widget=Widget.objects.first(),
            label={"en": "Name"},
        )

        report_config = ReportConfig(graph=self.graph)
        report_config.full_clean()

        key_data_summary = find_components(report_config.config, "KeyDataSummary")[0]
        self.assertEqual(
            key_data_summary["config"]["summary"][0],
            {"node_alias": "name_content", "label": {"en": "Name"}},
        )

    def test_descriptor_tokens_resolve_within_their_nodegroup(self):
        Node.objects.create(
            nodegroup=self.identifiers,
            name="Content",
            alias="content",
            graph=self.graph,
            istopnode=False,
            datatype="string",
        )
        Node.objects.create(
            nodegroup=self.description,
            name="content",
            alias="description_text",
            graph=self.graph,
            istopnode=False,
            datatype="string",
        )
        descriptor_function = FunctionXGraph.objects.get(graph=self.graph)
        descriptor_function.config["descriptor_types"]["description"][
            "string_template"
        ] = "<content>"
        descriptor_function.save()

        report_config = ReportConfig(graph=self.graph)
        report_config.full_clean()

        self.assertEqual(
            find_components(report_config.config, "ReportHeader")[0]["config"][
                "summary"
            ],
            [{"node_alias": "description_text", "label": "content"}],
        )

    def test_card_sections_cover_top_level_cards(self):
        sections = ReportConfig(graph=self.graph).generate_card_sections()

        self.assertEqual(
            [
                section["components"][0]["config"]["nodegroup_alias"]
                for section in sections
            ],
            ["identifiers", "production", "hidden_branch", "description"],
        )

    def test_related_resources_panel_lists_models_linked_either_way(self):
        linked_model = make_resource_model("linked_model", "Linked Model")
        linking_model = make_resource_model("linking_model", "Another Model")
        Node.objects.create(
            nodegroup=self.identifiers,
            name="Linked thing",
            alias="linked_thing",
            graph=self.graph,
            istopnode=False,
            datatype="resource-instance",
            config={"graphs": [{"graphid": str(linked_model.pk)}]},
        )
        linking_nodegroup = make_nodegroup(linking_model, "points_here_group")
        Node.objects.create(
            nodegroup=linking_nodegroup,
            name="Points here",
            alias="points_here",
            graph=linking_model,
            istopnode=False,
            datatype="resource-instance-list",
            config={"graphs": [{"graphid": str(self.graph.pk)}]},
        )

        photos_nodegroup = make_nodegroup(linked_model, "photos_group")
        make_node(linked_model, photos_nodegroup, "photos", "file-list")

        report_config = ReportConfig(graph=self.graph)
        report_config.full_clean()

        self.assertEqual(
            find_components(report_config.config, "RelatedResourcesPanel")[0]["config"][
                "graphs"
            ],
            ["linking_model", "linked_model"],
        )
        self.assertEqual(
            find_components(report_config.config, "ImagesPanel")[0]["config"]["images"],
            [{"model": "linked_model", "node": "photos"}],
        )

    def test_configs_that_contradict_the_graph_are_rejected(self):
        ReportConfig(graph=self.graph, config=curated_config()).full_clean()

        def mutate_unknown_nodegroup(config):
            find_components(config, "ReportFolio")[0]["config"][
                "nodegroup_alias"
            ] = "missing"

        def mutate_unknown_summary_node(config):
            find_components(config, "ReportHeader")[0]["config"]["summary"] = [
                {"node_alias": "missing", "label": "Missing"}
            ]

        def mutate_semantic_summary_node(config):
            find_components(config, "KeyDataSummary")[0]["config"]["summary"] = [
                {"node_alias": "production", "label": "Production"}
            ]

        def mutate_key_outside_config(config):
            find_components(config, "ReportSection")[0]["label"] = {"en": "Production"}

        def mutate_non_string_component(config):
            find_components(config, "ReportSection")[0]["component"] = None

        def mutate_non_dict_config(config):
            find_components(config, "ReportSection")[0]["config"] = []

        def mutate_renamed_component(config):
            config["components"][0]["component"] = "my_app/Reports/CustomReport"
            find_components(config, "ReportFolio")[0]["config"][
                "nodegroup_alias"
            ] = "missing"

        for mutation in (
            mutate_unknown_nodegroup,
            mutate_unknown_summary_node,
            mutate_semantic_summary_node,
            mutate_key_outside_config,
            mutate_non_string_component,
            mutate_non_dict_config,
            mutate_renamed_component,
        ):
            with self.subTest(mutation=mutation.__name__):
                config = curated_config()
                mutation(config)
                with self.assertRaises(ValidationError):
                    ReportConfig(graph=self.graph, config=config).full_clean()

    def test_empty_resource_report_config_is_valid(self):
        config = {
            "name": "Empty",
            "components": [{"component": RESOURCE_REPORT_COMPONENT, "config": {}}],
        }

        ReportConfig(graph=self.graph, config=config).full_clean()

    def test_nodegroup_aliases_may_name_any_node_in_the_nodegroup(self):
        config = curated_config()
        find_components(config, "ReportFolio")[0]["config"][
            "nodegroup_alias"
        ] = "name_content"

        ReportConfig(graph=self.graph, config=config).full_clean()

    def test_sections_about_another_graph_skip_report_graph_checks(self):
        config = curated_config()
        resource_report_config_from(config)["components"].append(
            report_component(
                "ReportSection",
                {
                    "graph_slug": "other_model",
                    "components": [
                        report_component(
                            "ReportFolio", {"nodegroup_alias": "not_in_this_graph"}
                        )
                    ],
                },
            )
        )

        ReportConfig(graph=self.graph, config=config).full_clean()

    def prune(self, config, readable_nodegroups, writable_nodegroups=()):
        report_config = ReportConfig(graph=self.graph, config=config)
        return update_report_configuration_with_nodegroup_permissions(
            report_configuration_instance=report_config,
            report_nodegroup_ids_with_user_read_permission={
                nodegroup.pk for nodegroup in readable_nodegroups
            },
            report_nodegroup_ids_with_user_write_permission={
                nodegroup.pk for nodegroup in writable_nodegroups
            },
        )

    def test_legacy_pruning_drops_unreadable_sections_and_flags_writable_ones(self):
        config = legacy_config(
            data_section("identifiers", ["identifier_content"]),
            data_section("production", ["name_content", "type"]),
        )

        pruned = self.prune(
            config,
            readable_nodegroups=[self.identifiers, self.production],
            writable_nodegroups=[self.identifiers],
        )
        self.assertEqual(
            [
                (
                    component["config"]["nodegroup_alias"],
                    component["config"]["has_write_permission"],
                )
                for component in pruned["components"]
            ],
            [("identifiers", True), ("production", False)],
        )

        pruned = self.prune(config, readable_nodegroups=[self.identifiers])
        self.assertEqual(
            [
                component["config"]["nodegroup_alias"]
                for component in pruned["components"]
            ],
            ["identifiers"],
        )

    def test_legacy_pruning_filters_node_aliases(self):
        linked_section = {
            "component": "my_app/LinkedSection",
            "config": {
                "graph_slug": "other_model",
                "node_aliases": ["location_geometry"],
            },
        }
        unlinked_section = {
            "component": "my_app/NodeList",
            "config": {"node_aliases": ["location_geometry"]},
        }
        config = legacy_config(
            data_section("production", ["name_content", "location_geometry"]),
            linked_section,
            unlinked_section,
        )

        pruned = self.prune(config, readable_nodegroups=[self.production])

        self.assertEqual(
            [component["component"] for component in pruned["components"]],
            [
                "arches_modular_reports/ModularReport/components/DataSection",
                "my_app/LinkedSection",
            ],
        )
        self.assertEqual(
            pruned["components"][0]["config"]["node_aliases"], ["name_content"]
        )
        self.assertEqual(pruned["components"][1]["config"]["node_aliases"], [])

    def test_legacy_pruning_drops_emptied_sections_and_keeps_empty_filters(self):
        config = legacy_config(
            {
                "component": "my_app/LinkedSections",
                "config": {
                    "sections": [
                        {
                            "name": "General",
                            "components": [
                                data_section(
                                    "identifiers", ["identifier_content"], filters=[]
                                )
                            ],
                        },
                        {
                            "name": "Production",
                            "components": [
                                data_section("production", ["name_content"])
                            ],
                        },
                    ]
                },
            }
        )

        pruned = self.prune(config, readable_nodegroups=[self.identifiers])

        sections = pruned["components"][0]["config"]["sections"]
        self.assertEqual([section["name"] for section in sections], ["General"])
        self.assertEqual(sections[0]["components"][0]["config"]["filters"], [])

    def test_legacy_pruning_strips_unreadable_descriptor_tokens(self):
        config = legacy_config(
            {
                "component": "my_app/DescriptorSection",
                "config": {"descriptor": "<name_content> (<identifier_content>)"},
            }
        )

        pruned = self.prune(config, readable_nodegroups=[self.identifiers])

        self.assertEqual(
            pruned["components"][0]["config"]["descriptor"], " (<identifier_content>)"
        )

    def test_legacy_pruning_returns_nothing_when_no_component_is_readable(self):
        config = legacy_config(data_section("production", ["name_content"]))

        self.assertIsNone(self.prune(config, readable_nodegroups=[]))

    def test_pruning_removes_unreadable_folios_summaries_and_emptied_containers(self):
        pruned = self.prune(curated_config(), [self.identifiers])

        self.assertEqual(
            [
                folio["config"]["nodegroup_alias"]
                for folio in find_components(pruned, "ReportFolio")
            ],
            ["identifiers"],
        )
        self.assertEqual(
            [
                section["config"]["label"]
                for section in find_components(pruned, "ReportSection")
            ],
            [{"en": "Identifiers"}],
        )
        self.assertEqual(
            find_components(pruned, "ReportHeader")[0]["config"]["summary"], []
        )
        self.assertEqual(
            find_components(pruned, "KeyDataSummary")[0]["config"]["summary"],
            [{"node_alias": "identifier_content", "label": "Identifier"}],
        )

        pruned = self.prune(curated_config(), [])

        split_pane = find_components(pruned, "SplitPane")[0]
        self.assertEqual(split_pane["config"]["main"], [])
        self.assertEqual(
            [child["component"] for child in split_pane["config"]["aside"]],
            [component_path("KeyDataSummary")],
        )
        self.assertEqual(
            find_components(pruned, "KeyDataSummary")[0]["config"]["summary"], []
        )
