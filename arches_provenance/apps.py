from django.apps import AppConfig
from arches.settings_utils import generate_frontend_configuration


class ArchesProvenanceConfig(AppConfig):
    name = "arches_provenance"
    is_arches_application = True

    def ready(self):
        from arches.app.models.system_settings import settings
        if settings.APP_NAME.lower() == self.name:
            generate_frontend_configuration()
