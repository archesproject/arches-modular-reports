from http import HTTPStatus

from django.core.paginator import Paginator
from django.db.models import Prefetch
from django.http import Http404
from django.shortcuts import render
from django.utils import translation
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.generic import View

from arches.app.views.api import APIBase
from arches.app.models import models
from arches.app.models.tile import Tile
from arches.app.models.card import Card
from arches.app.utils.decorators import can_read_resource_instance
from arches.app.utils.label_based_graph_v2 import LabelBasedGraph
from arches.app.utils.permission_backend import get_nodegroups_by_perm
from arches.app.utils.response import JSONErrorResponse, JSONResponse
from arches.app.views.resource import ResourceReportView

from arches_provenance.models import ReportConfig

from arches_provenance.app.utils.label_based_graph_override import (
    LabelBasedGraphWithBranchExport,
)
from arches_provenance.app.utils.nodegroup_tile_data_utils import (
    get_sorted_filtered_tiles,
)


@method_decorator(can_read_resource_instance, name="dispatch")
class ProvenanceEditableReportConfigView(View):
    def get(self, request):
        """Just get first. But if there are multiple in the future,
        the vue component will need to know which one to request."""
        result = ReportConfig.objects.filter(
            graph__resourceinstance=request.GET.get("resourceId")
        ).first()
        if not result:
            return JSONErrorResponse(
                _("No report config found."), status=HTTPStatus.NOT_FOUND
            )
        # Config might expose nodegroup existence: TODO: check permissions?
        return JSONResponse(result.config)


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
            context = self.get_context_data(
                main_script="views/resource/report",
                resourceid=resourceid,
                templateid=graph.template.pk,
                # To the extent possible, avoid DB queries needed for KO
                report_templates=models.ReportTemplate.objects.filter(
                    componentname="editable-report"
                ),
                card_components=models.CardComponent.objects.none(),
                widgets=models.Widget.objects.none(),
                map_markers=models.MapMarker.objects.none(),
                geocoding_providers=models.Geocoder.objects.none(),
            )
        else:
            template = "views/resource/report.htm"
            context = self.get_context_data(
                main_script="views/resource/report",
                resourceid=resourceid,
                report_templates=models.ReportTemplate.objects.all(),
                card_components=models.CardComponent.objects.all(),
                widgets=models.Widget.objects.all(),
                map_markers=models.MapMarker.objects.all(),
                geocoding_providers=models.Geocoder.objects.all(),
            )

        if graph.iconclass:
            context["nav"]["icon"] = graph.iconclass
        context["nav"]["title"] = graph.name
        context["nav"]["res_edit"] = True
        context["nav"]["print"] = True

        return render(request, template, context)


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
            .prefetch_related("nodegroup__cardmodel_set")
            .prefetch_related(
                Prefetch(
                    "cardxnodexwidget_set",
                    queryset=models.CardXNodeXWidget.objects.order_by("sortorder"),
                )
            )
        )

        return JSONResponse(
            {
                node.alias: {
                    "nodeid": node.nodeid,
                    "name": node.name,
                    "card_name": node.nodegroup.cardmodel_set[0].name,
                    "widget_label": (
                        node.cardxnodexwidget_set.all()[0].label
                        if node.cardxnodexwidget_set.all()
                        else node.name.replace("_", " ").title()
                    ),
                    "datatype": node.datatype,
                }
                for node in nodes
            }
        )


@method_decorator(can_read_resource_instance, name="dispatch")
class NodegroupTileDataView(APIBase):
    def get(self, request, resourceinstanceid, nodegroupid):
        page_number = request.GET.get("page")
        rows_per_page = request.GET.get("rows_per_page")

        query = request.GET.get("query")
        sort_node_id = request.GET.get("sort_node_id")
        sort_order = request.GET.get("sort_order", "asc")

        user_language = translation.get_language()

        tiles = get_sorted_filtered_tiles(
            resourceinstanceid=resourceinstanceid,
            nodegroupid=nodegroupid,
            sort_node_id=sort_node_id,
            sort_order=sort_order,
            query=query,
            user_language=user_language,
        )

        paginator = Paginator(tiles, rows_per_page)
        page = paginator.page(page_number)

        # BEGIN serializer logic
        node = models.Node.objects.select_related("graph__publication").get(
            pk=nodegroupid
        )

        published_graph = models.PublishedGraph.objects.get(
            publication=node.graph.publication, language=user_language
        )

        node_ids_to_tiles_reference = {}
        for tile in page.object_list:
            node_ids = list(tile.data.keys())

            if str(tile.nodegroup_id) not in node_ids:
                node_ids.append(str(tile.nodegroup_id))

            for node_id in node_ids:
                tile_list = node_ids_to_tiles_reference.get(node_id, [])
                tile_list.append(tile)
                node_ids_to_tiles_reference[node_id] = tile_list
        # END serializer logic

        response_data = {
            "results": [
                LabelBasedGraph.from_tile(
                    tile,
                    node_ids_to_tiles_reference,
                    nodegroup_cardinality_reference={},
                    serialized_graph=published_graph.serialized_graph,
                )
                for tile in page.object_list
            ],
            "total_count": paginator.count,
            "page": page_number,
        }

        return JSONResponse(response_data)


@method_decorator(can_read_resource_instance, name="dispatch")
class ChildTileDataView(APIBase):
    def get(self, request, tileid):
        tile = (
            models.TileModel.objects.filter(tileid=tileid)
            .select_related("resourceinstance__graph__publication")
            .get()
        )
        published_graph = models.PublishedGraph.objects.get(
            publication=tile.resourceinstance.graph.publication,
            language=translation.get_language(),
        )
        serialized_graph = published_graph.serialized_graph
        return JSONResponse(
            self._serialize_with_children(tile, serialized_graph)["@children"]
        )

    def _serialize_with_children(self, tile, serialized_graph):
        node_ids = list(tile.data.keys())

        if str(tile.nodegroup_id) not in node_ids:
            node_ids.append(str(tile.nodegroup_id))

        node_ids_to_tiles_reference = {}
        for node_id in node_ids:
            tile_list = node_ids_to_tiles_reference.get(node_id, [])
            tile_list.append(tile)
            node_ids_to_tiles_reference[node_id] = tile_list

        tile._children = [
            self._serialize_with_children(child, serialized_graph)
            for child in tile.tilemodel_set.order_by("sortorder")
        ]

        return {
            "@children": tile._children,
            **LabelBasedGraphWithBranchExport.from_tile(
                tile, node_ids_to_tiles_reference, {}, serialized_graph=serialized_graph
            ),
        }


class CardFromNodegroupIdView(APIBase):
    def get(self, request, nodegroupid):
        try:
            card = Card.objects.get(nodegroup_id=nodegroupid)
        except models.Card.DoesNotExist:
            return JSONErrorResponse(status=HTTPStatus.NOT_FOUND)

        return JSONResponse(card)
