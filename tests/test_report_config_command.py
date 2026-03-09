import json
import os
import uuid
from io import StringIO
from unittest.mock import patch

from arches import __version__ as _arches_version_str
from arches.app.models.graph import Graph
from arches.app.models.models import Node, NodeGroup
from arches_modular_reports.models import ReportConfig
from django.core import management
from django.test import TestCase
from packaging.version import Version

import arches_modular_reports.config_generator_registry as registry_module
from arches_modular_reports.config_generator_registry import register

arches_version = Version(_arches_version_str)


def _make_graph(slug):
    """Create a non-draft resource graph with the given slug."""
    if arches_version < Version("8.0"):
        g = Graph.new(is_resource=True)
        g.slug = slug
        g.save()
    else:
        g = Graph.objects.create_graph(is_resource=True, slug=slug)
        Graph.objects.filter(slug=slug).exclude(source_identifier=None).delete()
    return Graph.objects.get(slug=slug)


class ReportConfigCommandTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        if arches_version < Version("8.0"):
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


class GenerateReportConfigCommandTests(TestCase):
    """Tests for the `report_configs generate` management command."""

    @classmethod
    def setUpTestData(cls):
        cls.graph = _make_graph("gen_test_graph")
        cls.other_graph = _make_graph("gen_other_graph")

    def setUp(self):
        self._saved_registry = dict(registry_module._registry)
        register(
            "test_gen",
            lambda graph: {
                "name": f"Generated for {graph.slug}",
                "theme": "",
                "components": [],
            },
        )

    def tearDown(self):
        registry_module._registry.clear()
        registry_module._registry.update(self._saved_registry)

    # --- happy-path creation ---

    def test_generate_creates_config_for_registered_generator(self):
        management.call_command("report_configs", "generate", graph="gen_test_graph")
        self.assertTrue(
            ReportConfig.objects.filter(graph=self.graph, slug="test_gen").exists()
        )

    def test_generated_config_content_comes_from_factory(self):
        management.call_command("report_configs", "generate", graph="gen_test_graph")
        rc = ReportConfig.objects.get(graph=self.graph, slug="test_gen")
        self.assertEqual(rc.config["name"], "Generated for gen_test_graph")

    def test_generate_reports_created_status_to_stdout(self):
        stdout = StringIO()
        management.call_command(
            "report_configs", "generate", graph="gen_test_graph", stdout=stdout
        )
        self.assertIn("Created", stdout.getvalue())

    # --- idempotency (no --overwrite) ---

    def test_generate_skips_existing_config_without_overwrite(self):
        management.call_command("report_configs", "generate", graph="gen_test_graph")
        rc = ReportConfig.objects.get(graph=self.graph, slug="test_gen")
        rc.config["name"] = "Manually changed"
        rc.save()

        management.call_command("report_configs", "generate", graph="gen_test_graph")

        rc.refresh_from_db()
        self.assertEqual(rc.config["name"], "Manually changed")

    def test_generate_reports_skipped_status_to_stdout(self):
        management.call_command("report_configs", "generate", graph="gen_test_graph")
        stdout = StringIO()
        management.call_command(
            "report_configs", "generate", graph="gen_test_graph", stdout=stdout
        )
        self.assertIn("Skipped", stdout.getvalue())

    # --- --overwrite confirmed ---

    def test_generate_overwrite_updates_existing_config(self):
        management.call_command("report_configs", "generate", graph="gen_test_graph")
        rc = ReportConfig.objects.get(graph=self.graph, slug="test_gen")
        rc.config["name"] = "Manually changed"
        rc.save()

        with patch("builtins.input", return_value="y"):
            management.call_command(
                "report_configs", "generate", graph="gen_test_graph", overwrite=True
            )

        rc.refresh_from_db()
        self.assertEqual(rc.config["name"], "Generated for gen_test_graph")

    def test_generate_overwrite_reports_overwritten_status_to_stdout(self):
        management.call_command("report_configs", "generate", graph="gen_test_graph")
        stdout = StringIO()
        with patch("builtins.input", return_value="y"):
            management.call_command(
                "report_configs",
                "generate",
                graph="gen_test_graph",
                overwrite=True,
                stdout=stdout,
            )
        self.assertIn("Overwritten", stdout.getvalue())

    # --- --overwrite aborted ---

    def test_generate_overwrite_aborts_when_user_declines(self):
        management.call_command("report_configs", "generate", graph="gen_test_graph")
        rc = ReportConfig.objects.get(graph=self.graph, slug="test_gen")
        rc.config["name"] = "Manually changed"
        rc.save()

        with patch("builtins.input", return_value="n"):
            management.call_command(
                "report_configs", "generate", graph="gen_test_graph", overwrite=True
            )

        rc.refresh_from_db()
        self.assertEqual(rc.config["name"], "Manually changed")

    def test_generate_overwrite_abort_writes_message_to_stdout(self):
        management.call_command("report_configs", "generate", graph="gen_test_graph")
        stdout = StringIO()
        with patch("builtins.input", return_value="n"):
            management.call_command(
                "report_configs",
                "generate",
                graph="gen_test_graph",
                overwrite=True,
                stdout=stdout,
            )
        self.assertIn("Aborted", stdout.getvalue())

    # --- graph targeting ---

    def test_generate_with_specific_slug_only_affects_that_graph(self):
        management.call_command("report_configs", "generate", graph="gen_test_graph")
        self.assertTrue(
            ReportConfig.objects.filter(graph=self.graph, slug="test_gen").exists()
        )
        self.assertFalse(
            ReportConfig.objects.filter(
                graph=self.other_graph, slug="test_gen"
            ).exists()
        )

    def test_generate_without_slug_creates_configs_for_all_eligible_graphs(self):
        management.call_command("report_configs", "generate")
        self.assertTrue(
            ReportConfig.objects.filter(graph=self.graph, slug="test_gen").exists()
        )
        self.assertTrue(
            ReportConfig.objects.filter(
                graph=self.other_graph, slug="test_gen"
            ).exists()
        )

    def test_generate_unknown_graph_slug_writes_error_and_creates_nothing(self):
        stderr = StringIO()
        management.call_command(
            "report_configs",
            "generate",
            graph="totally_nonexistent_slug",
            stderr=stderr,
        )
        self.assertFalse(ReportConfig.objects.filter(slug="test_gen").exists())
        self.assertIn("totally_nonexistent_slug", stderr.getvalue())

    # --- no generators registered ---

    def test_generate_with_empty_registry_writes_message_and_creates_nothing(self):
        registry_module._registry.clear()
        stdout = StringIO()
        management.call_command("report_configs", "generate", stdout=stdout)
        self.assertFalse(ReportConfig.objects.filter(graph=self.graph).exists())
        self.assertIn("No config generators registered", stdout.getvalue())
