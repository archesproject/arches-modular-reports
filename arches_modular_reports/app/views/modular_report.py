import json
from http import HTTPStatus

from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404
from django.shortcuts import render
from django.urls import reverse
from django.utils import translation
from django.utils.decorators import method_decorator
from django.utils.translation import get_language, get_language_info, gettext as _
from django.views.generic import View

from arches import VERSION as arches_version
from arches.app.datatypes.concept_types import BaseConceptDataType
from arches.app.models import models
from arches.app.utils.betterJSONSerializer import JSONDeserializer
from arches.app.utils.decorators import can_read_resource_instance
from arches.app.utils.permission_backend import get_nodegroups_by_perm, group_required
from arches.app.utils.response import JSONErrorResponse, JSONResponse
from arches.app.views.api import APIBase
from arches.app.views.base import MapBaseManagerView
from arches.app.views.resource import ResourceReportView

from arches_modular_reports.app.utils.decorators import can_read_nodegroup
from arches_modular_reports.models import ReportConfig

from arches_modular_reports.app.utils.update_report_configuration_for_nodegroup_permissions import (
    update_report_configuration_for_nodegroup_permissions,
)

from arches_modular_reports.app.utils.nodegroup_tile_data_utils import (
    annotate_node_values,
    annotate_related_graph_nodes_with_widget_labels,
    array_from_string,
    build_valueid_annotation,
    get_sorted_filtered_relations,
    get_sorted_filtered_tiles,
    prepare_links,
)


@method_decorator(can_read_resource_instance, name="dispatch")
class ModularReportConfigView(View):
    def get(self, request):
        filters = Q(graph__resourceinstance=request.GET.get("resourceId"))

        if arches_version >= (8, 0):
            filters &= Q(graph__source_identifier=None)

        slug = request.GET.get("slug", None)
        if slug:
            filters &= Q(slug__iexact=slug)
        else:
            filters &= Q(slug__iexact="default")

        config_instance = (
            ReportConfig.objects.select_related("graph")
            .prefetch_related("graph__node_set", "graph__node_set__nodegroup")
            .get(filters)
        )

        if not config_instance:
            return JSONErrorResponse(
                _("No report config found."), status=HTTPStatus.NOT_FOUND
            )

        return JSONResponse(
            update_report_configuration_for_nodegroup_permissions(
                config_instance, request.user
            )
        )


@method_decorator(can_read_resource_instance, name="dispatch")
class ModularReportAwareResourceReportView(ResourceReportView):
    def get(self, request, resourceid=None):
        graph = (
            models.GraphModel.objects.filter(resourceinstance=resourceid)
            .select_related("template")
            .first()
        )
        if not graph:
            raise Http404(
                _("No active report template is available for this resource.")
            )

        if graph.template.componentname == "modular-report":
            template = "views/resource/modular_report.htm"
            # Skip a few queries by jumping over the MapBaseManagerView
            # and calling its parent. This report doesn't use a map.
            context = super(MapBaseManagerView, self).get_context_data(
                main_script="views/resource/report",
                resourceid=resourceid,
                templateid=graph.template.pk,
                graph_slug=graph.slug,
                # To the extent possible, avoid DB queries needed for KO
                report_templates=[graph.template],
                card_components=models.CardComponent.objects.none(),
                widgets=models.Widget.objects.none(),
                map_markers=models.MapMarker.objects.none(),
                geocoding_providers=models.Geocoder.objects.none(),
            )
        else:
            name_resource = (
                models.ResourceInstance.objects.only("name")
                .get(resourceinstanceid=str(resourceid))
                .name
            )
            template = "views/resource/report.htm"
            context = self.get_context_data(
                main_script="views/resource/report",
                resourceid=resourceid,
                report_templates=models.ReportTemplate.objects.all(),
                card_components=models.CardComponent.objects.all(),
                widgets=models.Widget.objects.all(),
                map_markers=models.MapMarker.objects.all(),
                geocoding_providers=models.Geocoder.objects.all(),
                graph_name=graph.name,
                name_resource=name_resource,
            )

        if graph.iconclass:
            context["nav"]["icon"] = graph.iconclass
        context["nav"]["title"] = graph.name
        context["nav"]["res_edit"] = True
        context["nav"]["print"] = True

        return render(request, template, context)


@method_decorator(can_read_resource_instance, name="dispatch")
class RelatedResourceView(APIBase):
    def get(self, request, resourceid, related_graph_slug):
        try:
            resource = models.ResourceInstance.objects.get(pk=resourceid)
            filters = Q(slug=related_graph_slug)
            if arches_version >= (8, 0):
                filters &= Q(source_identifier=None)
            related_graph = models.GraphModel.objects.get(filters)
        except (models.ResourceInstance.DoesNotExist, models.GraphModel.DoesNotExist):
            return JSONErrorResponse(status=HTTPStatus.NOT_FOUND)

        additional_nodes = request.GET.get("node_aliases", "").split(",")
        page_number = request.GET.get("page", 1)
        rows_per_page = request.GET.get("rows_per_page", 10)
        sort_field = request.GET.get("sort_field", "@relation_name")
        direction = request.GET.get("direction", "asc")
        query = request.GET.get("query", "")
        request_language = translation.get_language()

        permitted_nodegroups = get_nodegroups_by_perm(
            request.user, "models.read_nodegroup"
        )
        is_user_rdm_admin = group_required(request.user, "RDM Administrator")

        nodes = annotate_related_graph_nodes_with_widget_labels(
            additional_nodes, related_graph, request_language
        )
        relations = get_sorted_filtered_relations(
            resource=resource,
            related_graph=related_graph,
            nodes=nodes,
            permitted_nodegroups=permitted_nodegroups,
            sort_field=sort_field,
            direction=direction,
            query=query,
            request_language=request_language,
        )
        paginator = Paginator(relations, rows_per_page)
        result_page = paginator.get_page(page_number)

        def make_resource_report_link(relation):
            nonlocal resourceid
            # Both sides are UUID python types (from ORM, or from route)
            if arches_version < (8, 0):
                if relation.resourceinstanceidfrom_id == resourceid:
                    target = relation.resourceinstanceidto_id
                else:
                    target = relation.resourceinstanceidfrom_id
            else:
                if relation.from_resource_id == resourceid:
                    target = relation.to_resource_id
                else:
                    target = relation.from_resource_id
            return reverse("resource_report", args=[target])

        value_finder = BaseConceptDataType()  # fetches serially, but caches.

        response_data = {
            "results": [
                {
                    "@relation_name": {
                        "display_value": getattr(relation, "@relation_name"),
                        "links": [],
                    },
                    "@display_name": {
                        "display_value": getattr(relation, "@display_name"),
                        "links": [
                            {
                                "label": getattr(relation, "@display_name"),
                                "link": make_resource_report_link(relation),
                            }
                        ],
                    },
                    **{
                        node.alias: {
                            "display_value": getattr(relation, node.alias),
                            "links": prepare_links(
                                node=node,
                                tile_values=getattr(
                                    relation, node.alias + "_instance_details", []
                                ),
                                node_display_value=getattr(relation, node.alias),
                                request_language=request_language,
                                value_finder=value_finder,
                                is_user_rdm_admin=is_user_rdm_admin,
                            ),
                        }
                        for node in nodes
                    },
                }
                for relation in result_page
            ],
            "graph_name": related_graph.name,
            "widget_labels": {node.alias: node.widget_label for node in nodes},
            "total_count": paginator.count,
            "page": result_page.number,
        }

        return JSONResponse(response_data)


class NodePresentationView(APIBase):
    @method_decorator(can_read_resource_instance, name="dispatch")
    def get(self, request, resourceid):
        try:
            graph = models.GraphModel.objects.filter(resourceinstance=resourceid).get()
        except models.GraphModel.DoesNotExist:
            return JSONErrorResponse(status=HTTPStatus.NOT_FOUND)
        permitted_nodegroups = get_nodegroups_by_perm(
            request.user, "models.read_nodegroup"
        )
        nodes = (
            models.Node.objects.filter(graph=graph)
            .filter(nodegroup__in=permitted_nodegroups)
            .select_related("nodegroup")
            .prefetch_related(
                "nodegroup__cardmodel_set",
                "cardxnodexwidget_set__widget",
            )
        )

        def getattr_from_queryset(queryset, attr, fallback):
            if queryset:
                return getattr(queryset[0], attr, fallback)
            return fallback

        def get_widget_name(queryset, fallback):
            if queryset and queryset[0].widget:
                return getattr(queryset[0].widget, "name", fallback)
            return fallback

        def get_widget_format(queryset, fallback=None):
            if fallback is None:
                fallback = {"format": "", "prefix": {}, "suffix": {}}
            if queryset and queryset[0].widget:
                if getattr(queryset[0].widget, "name", None) != "number-widget":
                    return fallback
                config = getattr(queryset[0], "config", None)
                if config:
                    ret = {
                        "format": config.get("format", fallback),
                        "prefix": config.get("prefix", fallback),
                        "suffix": config.get("suffix", fallback),
                    }
                    return ret
            return fallback

        def get_node_visibility(node):
            if node.pk == node.nodegroup.pk and node.nodegroup.cardmodel_set.all():
                return node.nodegroup.cardmodel_set.all()[0].visible
            if node.cardxnodexwidget_set.all():
                return node.cardxnodexwidget_set.all()[0].visible
            return True

        return JSONResponse(
            {
                node.alias: {
                    "nodeid": node.nodeid,
                    "name": node.name,
                    "card_name": getattr_from_queryset(
                        node.nodegroup.cardmodel_set.all(),
                        "name",
                        "",
                    ),
                    "card_order": getattr_from_queryset(
                        node.nodegroup.cardmodel_set.all(),
                        "sortorder",
                        0,
                    ),
                    "widget_label": getattr_from_queryset(
                        node.cardxnodexwidget_set.all(),
                        "label",
                        node.name.replace("_", " ").title(),
                    ),
                    "widget_order": getattr_from_queryset(
                        node.cardxnodexwidget_set.all(),
                        "sortorder",
                        0,
                    ),
                    "visible": get_node_visibility(node),
                    "nodegroup": {
                        "nodegroup_id": node.nodegroup.pk,
                        "cardinality": node.nodegroup.cardinality,
                    },
                    "is_rich_text": get_widget_name(
                        node.cardxnodexwidget_set.all(), None
                    )
                    == "rich-text-widget",
                    "is_numeric": get_widget_name(node.cardxnodexwidget_set.all(), None)
                    == "number-widget",
                    "number_format": get_widget_format(node.cardxnodexwidget_set.all()),
                }
                for node in nodes
            }
        )


@method_decorator(can_read_resource_instance, name="dispatch")
@method_decorator(can_read_nodegroup, name="dispatch")
class NodegroupTileDataView(APIBase):
    def get(self, request, resourceid, nodegroup_alias):
        page_number = request.GET.get("page")
        rows_per_page = request.GET.get("rows_per_page")
        filters = request.GET.get("filters", None)
        query = request.GET.get("query")
        sort_node_id = request.GET.get("sort_node_id")
        direction = request.GET.get("direction", "asc")

        filters = JSONDeserializer().deserialize(filters) if filters else None

        user_language = translation.get_language()

        is_user_rdm_admin = group_required(request.user, "RDM Administrator")

        tiles = get_sorted_filtered_tiles(
            resourceinstanceid=resourceid,
            nodegroup_alias=nodegroup_alias,
            sort_node_id=sort_node_id,
            direction=direction,
            query=query,
            user_language=user_language,
            user=request.user,
            filters=filters,
        )

        paginator = Paginator(tiles, rows_per_page)
        page = paginator.page(page_number)

        response_data = {
            "results": [
                {
                    **{
                        key: build_valueid_annotation(
                            value, is_user_rdm_admin, user_language
                        )
                        for key, value in tile.alias_annotations.items()
                    },
                    "@has_children": tile.has_children,
                    "@tile_id": tile.tileid,
                }
                for tile in page.object_list
            ],
            "total_count": paginator.count,
            "page": page.number,
        }

        return JSONResponse(response_data)


@method_decorator(can_read_resource_instance, name="dispatch")
class NodeTileDataView(APIBase):
    def get(self, request, resourceid):
        permitted_nodegroups = get_nodegroups_by_perm(request.user, "read_nodegroup")
        node_aliases = request.GET.getlist("node_alias", [])
        user_lang = translation.get_language()
        tile_limit = int(request.GET.get("tile_limit", 0))

        is_user_rdm_admin = group_required(request.user, "RDM Administrator")

        nodes_with_display_data = annotate_node_values(
            node_aliases, resourceid, permitted_nodegroups, user_lang, tile_limit
        )
        value_finder = BaseConceptDataType()

        return JSONResponse(
            {
                node.alias: [
                    {
                        "display_values": array_from_string(
                            display_object["display_value"]
                        ),
                        "links": prepare_links(
                            node,
                            [display_object["tile_value"]],
                            display_object["display_value"],
                            user_lang,
                            value_finder,
                            is_user_rdm_admin,
                        ),
                    }
                    for display_object in node.display_data
                ]
                for node in nodes_with_display_data
            }
        )


class UserPermissionsView(APIBase):
    def get(self, request):
        reqested_permissions = json.loads(request.GET.get("permissions", "[]"))
        user_permissions = {}
        for permission in reqested_permissions:
            if permission == "RDM Administrator":
                user_permissions[permission] = group_required(request.user, permission)
        return JSONResponse(user_permissions)


class LanguageSettingsView(APIBase):
    def get(self, request):
        return JSONResponse(
            {
                "language": get_language(),
                "language_dir": (
                    "ltr" if not get_language_info(get_language())["bidi"] else "rtl"
                ),
            }
        )
