from django.urls import include, path, re_path

from arches.app.models.system_settings import settings

from arches_modular_reports.app.views.modular_report import (
    EditHistoryView,
    ModularReportAwareResourceReportView,
    GraphSlugFromIdView,
    NodegroupTileDataView,
    NodePresentationView,
    ModularReportConfigView,
    RelatedResourceGroupsView,
    ReportContextView,
    UserPermissionsView,
)

uuid_regex = settings.UUID_REGEX

urlpatterns = [
    path(
        "modular_report_config",
        ModularReportConfigView.as_view(),
        name="modular_report_config",
    ),
    # Override core arches resource report view to allow rendering
    # distinct template for modular reports.
    path(
        "report/<uuid:resourceid>",
        ModularReportAwareResourceReportView.as_view(),
        name="resource_report",
    ),
    path(
        "report/<uuid:resourceid>/<str:report_config_slug>",
        ModularReportAwareResourceReportView.as_view(),
        name="resource_report",
    ),
    path(
        "api/graph_slug/<uuid:graphid>",
        GraphSlugFromIdView.as_view(),
        name="api_graph_slug",
    ),
    path(
        "api/report_context/<uuid:resourceid>",
        ReportContextView.as_view(),
        name="api_report_context",
    ),
    path(
        "api/edit_history/<uuid:resourceid>",
        EditHistoryView.as_view(),
        name="api_edit_history",
    ),
    path(
        "api/related_resource_groups/<uuid:resourceid>",
        RelatedResourceGroupsView.as_view(),
        name="api_related_resource_groups",
    ),
    path(
        "api/node_presentation/<uuid:resourceid>",
        NodePresentationView.as_view(),
        name="api_node_presentation",
    ),
    path(
        "api/nodegroup_tile_data/<uuid:resourceid>/<slug:nodegroup_alias>",
        NodegroupTileDataView.as_view(),
        name="api_nodegroup_tile_data",
    ),
    path(
        "api/has_permissions",
        UserPermissionsView.as_view(),
        name="api_has_permissions",
    ),
    path("", include("arches.extensions.querysets.urls")),
    path("", include("arches.extensions.vue_components.urls")),
]
