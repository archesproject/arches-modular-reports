import json
import os
import uuid
from arches import VERSION as arches_version
from arches.app.models.graph import Graph
from arches.app.models.models import Node, NodeGroup
from arches_modular_reports.models import ReportConfig
from django.core import management
from django.test import TestCase


class ReportConfigCommandTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        if arches_version < (8, 0):
            cls.graph = Graph.new(is_resource=True)
            cls.graph.slug = "test_graph"
            cls.graph.save()
        else:
            cls.graph = Graph.objects.create_graph(is_resource=True, slug="test_graph")
            Graph.objects.filter(slug="test_graph").exclude(
                source_identifier=None
            ).delete()  # delete draft graph

    def test_config_import_export(self):
        management.call_command(
            "report_configs",
            "load",
            source=os.path.join(
                os.getcwd(), "tests", "fixtures", "report_configs", self.graph.slug
            ),
        )
        with self.subTest():
            self.assertTrue(ReportConfig.objects.all().exists())

        with self.subTest():
            report_config = ReportConfig.objects.all().first()
            report_config.config["name"] = str(uuid.uuid1())
            report_config.save()
            dir_path = os.path.join(
                os.getcwd(), "tests", "fixtures", "report_configs", "tmp"
            )
            file_path = os.path.join(
                dir_path, self.graph.slug, f"{report_config.slug}.json"
            )
            management.call_command("report_configs", "write", dest=dir_path)
            with open(file_path) as f:
                d = json.load(f)
                self.assertTrue(d["name"] == report_config.config["name"])
