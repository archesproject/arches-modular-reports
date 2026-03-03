from django.apps import AppConfig
from django.db.models.signals import post_save
from arches.app.models.models import GraphModel
from arches_modular_reports.signals import handle_graph_post_save
from arches_modular_reports.config_generators import register
from arches_modular_reports.models import ReportConfig


class ArchesModularReportsConfig(AppConfig):
    name = "arches_modular_reports"
    verbose_name = "Arches Modular Reports"
    is_arches_application = True

    def ready(self):
        post_save.connect(handle_graph_post_save, sender=GraphModel)

        def _default_factory(graph):
            rc = ReportConfig(graph=graph)
            return rc.generate_config()

        register("default", _default_factory)
