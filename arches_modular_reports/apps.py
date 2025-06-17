from django.apps import AppConfig
from arches import VERSION as arches_version
from arches.settings_utils import generate_frontend_configuration

class ArchesModularReportsConfig(AppConfig):
    name = "arches_modular_reports"
    is_arches_application = True

    def ready(self):
        from arches.app.models.system_settings import settings

        if arches_version < (8, 0):
            if settings.APP_NAME.lower() == self.name:
                generate_frontend_configuration()