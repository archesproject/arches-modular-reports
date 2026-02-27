from arches import VERSION as arches_version
from arches_modular_reports.config_generators import get_all


def handle_graph_post_save(sender, instance, created, **kwargs):
    """Auto-create ReportConfig objects for newly created resource graphs.

    Iterates all registered config generators and creates a ReportConfig
    for each slug that doesn't already exist for this graph.
    """
    if not created or not instance.isresource or not instance.slug:
        return

    if arches_version >= (8, 0) and instance.source_identifier is not None:
        return

    from arches.app.models.system_settings import settings

    if str(instance.pk) == str(settings.SYSTEM_SETTINGS_RESOURCE_MODEL_ID):
        return

    from arches_modular_reports.models import ReportConfig

    for slug, factory in get_all().items():
        ReportConfig.objects.get_or_create(
            graph=instance,
            slug=slug,
            defaults={"config": factory(instance)},
        )
