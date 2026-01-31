from arches import VERSION as arches_version
from django.db.models import Q
from arches_modular_reports.models import ReportConfig


def get_report_config(resourceid, slug="default"):
    filters = Q(graph__resourceinstance=resourceid)
    filters &= Q(slug__iexact=slug)

    if arches_version >= (8, 0):
        filters &= Q(graph__source_identifier=None)

    config_instance = (
        ReportConfig.objects.select_related("graph")
        .prefetch_related("graph__node_set", "graph__node_set__nodegroup")
        .get(filters)
    )

    return config_instance
