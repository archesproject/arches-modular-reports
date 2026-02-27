from django.apps import AppConfig


class ArchesModularReportsConfig(AppConfig):
    name = "arches_modular_reports"
    verbose_name = "Arches Modular Reports"
    is_arches_application = True

    def ready(self):
        from django.db.models.signals import post_save
        from arches.app.models.models import GraphModel
        from arches_modular_reports.signals import handle_graph_post_save

        post_save.connect(handle_graph_post_save, sender=GraphModel)
