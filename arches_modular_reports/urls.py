from django.urls import include, path, re_path

from arches.app.models.system_settings import settings

from arches_modular_reports.app.views.modular_report import (
    ModularReportAwareResourceReportView,
    NodegroupTileDataView,
    NodePresentationView,
    NodeTileDataView,
    ModularReportConfigView,
    RelatedResourceView,
    UserPermissionsView,
    LanguageSettingsView,
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
    re_path(
        r"^report/(?P<resourceid>%s)$" % uuid_regex,
        ModularReportAwareResourceReportView.as_view(),
        name="resource_report",
    ),
    path(
        "api/related_resources/<uuid:resourceid>/<slug:related_graph_slug>",
        RelatedResourceView.as_view(),
        name="api_related_resources",
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
        "api/node_tile_data/<uuid:resourceid>",
        NodeTileDataView.as_view(),
        name="api_node_tile_data",
    ),
    path(
        "api/has_permissions",
        UserPermissionsView.as_view(),
        name="api_has_permissions",
    ),
    path(
        "api/client_language_settings",
        LanguageSettingsView.as_view(),
        name="api_client_language_settings",
    ),
    path("", include("arches_querysets.urls")),
    path("", include("arches_component_lab.urls")),
]
