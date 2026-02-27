"""
Registry for ReportConfig generators.

External packages can register config factory functions here by slug.
When a new resource graph is created, arches-modular-reports will call all
registered generators to auto-create ReportConfig objects for that graph.

Usage (e.g. in another package's AppConfig.ready()):

    from arches_modular_reports.config_generators import register
    register("my_slug", lambda graph: {"name": "My Config", "theme": "", "components": []})
"""

_registry: dict[str, callable] = {}


def register(slug: str, factory) -> None:
    """Register a config factory function for a given ReportConfig slug.

    Args:
        slug: The ReportConfig slug (e.g. "search", "map").
        factory: A callable that accepts a GraphModel instance and returns
                 a config dict compatible with ReportConfig.config.
    """
    _registry[slug] = factory


def get_all() -> dict:
    """Return a copy of all registered slug -> factory mappings."""
    return dict(_registry)
