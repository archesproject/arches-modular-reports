from arches import __version__ as _arches_version_str
from django.db.models import Q
from arches_modular_reports.models import ReportConfig
from packaging.version import Version

arches_version = Version(_arches_version_str)


def get_report_config(resourceid, slug="default"):
    filters = Q(graph__resourceinstance=resourceid)
    filters &= Q(slug__iexact=slug)

    if arches_version >= Version("8.0"):
        filters &= Q(graph__source_identifier=None)

    config_instance = (
        ReportConfig.objects.select_related("graph")
        .prefetch_related("graph__node_set", "graph__node_set__nodegroup")
        .get(filters)
    )

    return config_instance
