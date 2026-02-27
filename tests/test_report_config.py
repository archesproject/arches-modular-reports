import json

from django.core.exceptions import ValidationError
from django.test import TestCase

from arches import __version__ as _arches_version_str
from arches.app.models.graph import Graph
from arches.app.models.models import Node, NodeGroup

from arches_modular_reports.models import ReportConfig
from packaging.version import Version

arches_version = Version(_arches_version_str)


class ReportConfigTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        if arches_version < Version("8.0"):
            cls.graph = Graph.new(is_resource=True)
            cls.graph.slug = "test_graph"
            cls.graph.save()
        else:
            cls.graph = Graph.objects.create_graph(is_resource=True, slug="test_graph")

        nodegroup = NodeGroup.objects.create()
        grouping_node = Node.objects.create(
            pk=nodegroup.pk,
            name="Production",
            alias="production",
            graph=cls.graph,
            nodegroup=nodegroup,
            datatype="semantic",
            istopnode=False,
        )
        nodegroup.grouping_node = grouping_node
        nodegroup.save()

        Node.objects.create(
            nodegroup=nodegroup,
            name="Name content",
            alias="name_content",
            graph=cls.graph,
            istopnode=False,
            datatype="string",
        )
        Node.objects.create(
            nodegroup=nodegroup,
            name="Type",
            alias="type",
            graph=cls.graph,
            istopnode=False,
            datatype="concept",
        )
        Node.objects.create(
            nodegroup=nodegroup,
            name="Production Part Actor",
            alias="production_part_actor",
            graph=cls.graph,
            istopnode=False,
            datatype="resource-instance",
        )

    def test_header(self):
        header = ReportConfig(graph=self.graph)
        # Default config passes validation.
        header.full_clean()

        header.config = {
            "name": "Untitled Report",
            "components": [
                {
                    "config": {
                        "descriptor": "<name_content> [<type>], <production_part_actor>",
                        "node_alias_options": {
                            "production_part_actor": {
                                "limit": 3,
                                "separator": ",",
                            },
                        },
                    },
                    "component": "arches_modular_reports/ModularReport/components/ReportHeader",
                },
            ],
        }
        header.full_clean()

        invalid_config = json.loads(
            json.dumps(header.config).replace("limit", "garbage")
        )
        header.config = invalid_config
        with self.assertRaisesMessage(ValidationError, "Invalid option"):
            header.full_clean()
