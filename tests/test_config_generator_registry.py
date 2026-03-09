"""Tests for the config_generator_registry module.

The registry is a module-level dict, so each test saves and restores
the original contents to prevent cross-test pollution.
"""

from django.test import SimpleTestCase

import arches_modular_reports.config_generator_registry as registry_module
from arches_modular_reports.config_generator_registry import get_all, register


class ConfigGeneratorRegistryTests(SimpleTestCase):
    def setUp(self):
        self._saved = dict(registry_module._registry)

    def tearDown(self):
        registry_module._registry.clear()
        registry_module._registry.update(self._saved)

    # --- registration basics ---

    def test_register_appears_in_get_all(self):
        factory = lambda graph: {"name": "Test", "theme": "", "components": []}
        register("my_slug", factory)
        self.assertIn("my_slug", get_all())
        self.assertIs(get_all()["my_slug"], factory)

    def test_get_all_returns_copy_not_live_dict(self):
        """Mutating the returned dict must not affect the real registry."""
        snapshot = get_all()
        snapshot["injected"] = lambda g: {}
        self.assertNotIn("injected", registry_module._registry)

    def test_register_same_slug_twice_replaces_factory(self):
        first = lambda graph: {"name": "First"}
        second = lambda graph: {"name": "Second"}
        register("dupe", first)
        register("dupe", second)
        self.assertIs(get_all()["dupe"], second)

    def test_multiple_slugs_coexist(self):
        for slug in ("alpha", "beta", "gamma"):
            register(slug, lambda g: {})
        result = get_all()
        for slug in ("alpha", "beta", "gamma"):
            self.assertIn(slug, result)

    # --- factory contract ---

    def test_factory_receives_graph_as_sole_argument(self):
        calls = []

        def capturing_factory(graph):
            calls.append(graph)
            return {"name": "ok", "theme": "", "components": []}

        register("capture", capturing_factory)
        sentinel = object()
        get_all()["capture"](sentinel)
        self.assertEqual(calls, [sentinel])

    def test_factory_return_value_is_preserved(self):
        expected = {"name": "My Config", "theme": "dark", "components": []}
        register("return_test", lambda g: expected)
        self.assertEqual(get_all()["return_test"](None), expected)

    # --- default generator registered by AppConfig.ready() ---

    def test_default_generator_is_pre_registered(self):
        """apps.py should have already registered the 'default' slug."""
        self.assertIn("default", get_all())

    def test_default_factory_returns_dict(self):
        """The default factory must be callable but we can't pass a real
        graph here (no DB), so just verify it is a callable."""
        self.assertTrue(callable(get_all()["default"]))
