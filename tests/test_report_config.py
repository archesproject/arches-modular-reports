import json

from django.core.exceptions import ValidationError
from django.test import TestCase

from arches.app.models.graph import Graph
from arches.app.models.models import Node

from arches_provenance.models import ReportConfig


class ReportConfigTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.graph = Graph.new(is_resource=True)
        cls.graph.slug = "test_graph"
        cls.graph.save()
        Node.objects.create(
            alias="name_content", graph=cls.graph, istopnode=False, datatype="string"
        )
        Node.objects.create(
            alias="type", graph=cls.graph, istopnode=False, datatype="concept"
        )
        Node.objects.create(
            alias="production_part_actor",
            graph=cls.graph,
            istopnode=False,
            datatype="resource-instance",
        )

    def test_header(self):
        header = ReportConfig(graph=self.graph)
        header.clean()
        self.assertNotIn("node_alias_options", header.config["components"][0]["config"])

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
                    "component": "ReportHeader",
                },
            ],
        }
        header.clean()

        invalid_config = json.loads(
            json.dumps(header.config).replace("limit", "garbage")
        )
        header.config = invalid_config
        with self.assertRaisesMessage(ValidationError, "Invalid option"):
            header.clean()
