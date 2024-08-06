from django.apps import AppConfig

from arches.settings_utils import generate_frontend_configuration


class ArchesProvenanceConfig(AppConfig):
    name = "arches_provenance"
    is_arches_application = True

    def ready(self):
        generate_frontend_configuration()
