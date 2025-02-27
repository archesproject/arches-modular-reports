from http import HTTPStatus

from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import render
from django.urls import reverse
from django.utils import translation
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.generic import View

from arches.app.views.api import APIBase
from arches.app.models import models
from arches.app.utils.decorators import can_read_resource_instance
from arches.app.utils.permission_backend import (
    get_nodegroups_by_perm,
    user_can_read_resource,
)
from arches.app.utils.response import JSONErrorResponse, JSONResponse
from arches.app.views.base import MapBaseManagerView
from arches.app.views.resource import ResourceReportView

from arches_provenance.app.utils.decorators import can_read_nodegroup
from arches_provenance.models import ReportConfig

from arches_provenance.app.utils.update_report_configuration_for_nodegroup_permissions import (
    update_report_configuration_for_nodegroup_permissions,
)

from arches_provenance.app.utils.nodegroup_tile_data_utils import (
    annotate_node_values,
    annotate_related_graph_nodes_with_widget_labels,
    array_from_string,
    build_valueid_annotation,
    get_sorted_filtered_relations,
    get_sorted_filtered_tiles,
    prepare_links,
    serialize_tiles_with_children,
)


@method_decorator(can_read_resource_instance, name="dispatch")
class ProvenanceEditableReportConfigView(View):
    def get(self, request):
        """Just get first. But if there are multiple in the future,
        the vue component will need to know which one to request."""
        config_instance = (
            ReportConfig.objects.filter(
                graph__resourceinstance=request.GET.get("resourceId")
            )
            .select_related("graph")
            .first()
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
class EditableReportAwareResourceReportView(ResourceReportView):
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

        if graph.template.componentname == "editable-report":
            template = "views/resource/editable_report.htm"
            # Skip a few queries by jumping over the MapBaseManagerView
            # and calling its parent. This report doesn't use a map.
            context = super(MapBaseManagerView, self).get_context_data(
                main_script="views/resource/report",
                resourceid=resourceid,
                templateid=graph.template.pk,
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
            # TODO: arches v8: add source_identifier=None
            related_graph = models.GraphModel.objects.get(slug=related_graph_slug)
        except (models.ResourceInstance.DoesNotExist, models.GraphModel.DoesNotExist):
            return JSONErrorResponse(status=HTTPStatus.NOT_FOUND)

        additional_nodes = request.GET.get("nodes", "").split(",")
        page_number = request.GET.get("page", 1)
        rows_per_page = request.GET.get("rows_per_page", 10)
        sort_field = request.GET.get("sort_field", "@relation_name")
        direction = request.GET.get("direction", "asc")
        query = request.GET.get("query", "")
        request_language = translation.get_language()

        permitted_nodegroups = get_nodegroups_by_perm(
            request.user, "models.read_nodegroup"
        )
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
            if relation.resourceinstanceidfrom_id == resourceid:
                target = relation.resourceinstanceidto_id
            else:
                target = relation.resourceinstanceidfrom_id
            return reverse("resource_report", args=[target])

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
            .exclude(datatype__in={"annotation", "geojson-feature-collection"})
            .select_related("nodegroup")
            .prefetch_related(
                "nodegroup__cardmodel_set",
                "cardxnodexwidget_set",
            )
        )

        return JSONResponse(
            {
                node.alias: {
                    "nodeid": node.nodeid,
                    "name": node.name,
                    "card_name": (
                        node.nodegroup.cardmodel_set.all()[0].name
                        if node.nodegroup.cardmodel_set.all()
                        else None
                    ),
                    "widget_label": (
                        node.cardxnodexwidget_set.all()[0].label
                        if node.cardxnodexwidget_set.all()
                        else node.name.replace("_", " ").title()
                    ),
                    "nodegroup": {
                        "nodegroup_id": node.nodegroup.pk,
                        "cardinality": node.nodegroup.cardinality,
                    },
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

        query = request.GET.get("query")
        sort_node_id = request.GET.get("sort_node_id")
        direction = request.GET.get("direction", "asc")

        user_language = translation.get_language()

        tiles = get_sorted_filtered_tiles(
            resourceinstanceid=resourceid,
            nodegroup_alias=nodegroup_alias,
            sort_node_id=sort_node_id,
            direction=direction,
            query=query,
            user_language=user_language,
        )

        paginator = Paginator(tiles, rows_per_page)
        page = paginator.page(page_number)

        response_data = {
            "results": [
                {
                    **{
                        key: build_valueid_annotation(value)
                        for key, value in tile.alias_annotations.items()
                    },
                    # TODO: arches v8: tile.children.exists(),
                    "@has_children": tile.tilemodel_set.exists(),
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

        nodes_with_display_data = annotate_node_values(
            node_aliases, resourceid, permitted_nodegroups, user_lang, tile_limit
        )

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
                        ),
                    }
                    for display_object in node.display_data
                ]
                for node in nodes_with_display_data
            }
        )


class ChildTileDataView(APIBase):
    def get(self, request, tileid):
        tile = (
            models.TileModel.objects.filter(tileid=tileid)
            .select_related("resourceinstance__graph__publication")
            .get()
        )

        permitted_nodegroups = get_nodegroups_by_perm(
            request.user, "models.read_nodegroup"
        )
        if (
            not user_can_read_resource(request.user, str(tile.resourceinstance_id))
            or tile.nodegroup_id not in permitted_nodegroups
        ):
            return JSONErrorResponse(status=HTTPStatus.FORBIDDEN)

        published_graph = models.PublishedGraph.objects.get(
            publication=tile.resourceinstance.graph.publication,
            language=translation.get_language(),
        )

        configs = models.CardXNodeXWidget.objects.filter(
            node__graph=published_graph.serialized_graph["graphid"]
        ).select_related("card")
        card_visibility_reference = {
            str(config.node_id): config.card.visible if config.card else True
            for config in configs
        }
        node_visibility_reference = {
            str(config.node_id): config.visible for config in configs
        }

        serialized = serialize_tiles_with_children(
            tile=tile,
            serialized_graph=published_graph.serialized_graph,
            permitted_nodegroups=permitted_nodegroups,
            card_visibility_reference=card_visibility_reference,
            node_visibility_reference=node_visibility_reference,
        )

        return JSONResponse(serialized)
