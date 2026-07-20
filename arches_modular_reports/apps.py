from django.apps import AppConfig
from django.conf import settings

from arches.settings_utils import generate_frontend_configuration


class ArchesModularReportsConfig(AppConfig):
    name = "arches_modular_reports"
    verbose_name = "Arches Modular Reports"
    is_arches_application = True

    def ready(self):
        if settings.APP_NAME.lower() == self.name:
            generate_frontend_configuration()

        # Imports are deferred to ready() to avoid AppRegistryNotReady errors.
        # Django models cannot be imported at module level in AppConfig subclasses.
        from arches_modular_reports.config_generator_registry import register
        from arches_modular_reports.models import ReportConfig

        def _default_factory(graph):
            rc = ReportConfig(graph=graph)
            return rc.generate_config()

        register("default", _default_factory)
