from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
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
    path("", include("arches_querysets.urls")),
    path("", include("arches_component_lab.urls")),
]


# handler400 = "arches.app.views.main.custom_400"
# handler403 = "arches.app.views.main.custom_403"
# handler404 = "arches.app.views.main.custom_404"
# handler500 = "arches.app.views.main.custom_500"

# Ensure Arches core urls are superseded by project-level urls
urlpatterns.append(path("", include("arches.urls")))

# Adds URL pattern to serve media files during development
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Only handle i18n routing in active project. This will still handle the routes provided by Arches core and Arches applications,
# but handling i18n routes in multiple places causes application errors.
if settings.ROOT_URLCONF == __name__:
    if settings.SHOW_LANGUAGE_SWITCH is True:
        urlpatterns = i18n_patterns(*urlpatterns)

    urlpatterns.append(path("i18n/", include("django.conf.urls.i18n")))
