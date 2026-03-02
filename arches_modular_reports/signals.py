from arches import __version__ as _arches_version
from arches.app.models.system_settings import settings
from arches_modular_reports.config_generators import get_all
from arches_modular_reports.models import ReportConfig
from packaging.version import Version

arches_version = Version(_arches_version)

def handle_graph_post_save(sender, instance, created, **kwargs):
    """Auto-create ReportConfig objects for newly created resource graphs.

    Iterates all registered config generators and creates a ReportConfig
    for each slug that doesn't already exist for this graph.
    """
    if not created or not instance.isresource or not instance.slug:
        return

    if arches_version >= Version("8.0") and instance.source_identifier is not None:
        return

    if str(instance.pk) == str(settings.SYSTEM_SETTINGS_RESOURCE_MODEL_ID):
        return

    for slug, factory in get_all().items():
        ReportConfig.objects.get_or_create(
            graph=instance,
            slug=slug,
            defaults={"config": factory(instance)},
        )
