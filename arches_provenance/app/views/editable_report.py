from http import HTTPStatus

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models.functions import Concat
from django.db.models import Prefetch, Func, TextField, Value, F
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


class NodegroupTileDataView(APIBase):
    def get(self, request, resourceinstanceid, nodegroupid):
        class ArchesGetNodeDisplayValue(Func):
            function = "__arches_get_node_display_value"
            output_field = TextField()

            def __init__(self, in_tiledata, in_nodeid, language_id):
                super().__init__(in_tiledata, in_nodeid, language_id)

        user_language = translation.get_language()
        query = request.GET.get("query", "")
        sort_node_id = request.GET.get("sort_node_id")
        sort_order = request.GET.get("sort_order", "asc")

        # semantic, annotation, and geojson-feature-collection data types are excluded in __arches_get_node_display_value
        nodes = models.Node.objects.filter(nodegroup_id=nodegroupid).exclude(
            datatype__in=["semantic", "annotation", "geojson-feature-collection"]
        )

        annotations = {
            f'field_{str(node.pk).replace("-", "_")}': ArchesGetNodeDisplayValue(
                F("data"), Value(str(node.pk)), Value(user_language)
            )
            for node in nodes
        }

        # adds spaces between fields
        display_values_with_spaces = []
        for field in [F(field) for field in annotations.keys()]:
            display_values_with_spaces.append(field)
            display_values_with_spaces.append(Value(" "))

        tiles = (
            Tile.objects.filter(
                resourceinstance_id=resourceinstanceid, nodegroup_id=nodegroupid
            )
            .annotate(**annotations)
            .annotate(
                search_text=Concat(
                    *display_values_with_spaces, output_field=TextField()
                )
            )
            .filter(search_text__icontains=query)
        )

        if sort_node_id:
            sort_field_name = f'field_{sort_node_id.replace("-", "_")}'

            if sort_order == "asc":
                tiles = tiles.order_by(F(sort_field_name).asc())
            elif sort_order == "desc":
                tiles = tiles.order_by(F(sort_field_name).desc())

        page_number = request.GET.get("page")
        rows_per_page = request.GET.get("rows_per_page")

        try:
            page_number = int(page_number)
            rows_per_page = int(rows_per_page)
        except ValueError:
            return JSONResponse(
                {"error": "Invalid page or rows_per_page parameter"}, status=400
            )

        paginator = Paginator(tiles, rows_per_page)

        try:
            page = paginator.page(page_number)
        except PageNotAnInteger:
            page = paginator.page(1)
        except EmptyPage:
            page = paginator.page(paginator.num_pages)

        node_ids_to_tiles_reference = {}
        for tile in page.object_list:
            node_ids = list(tile.data.keys())

            if str(tile.nodegroup_id) not in node_ids:
                node_ids.append(str(tile.nodegroup_id))

            for node_id in node_ids:
                tile_list = node_ids_to_tiles_reference.get(node_id, [])
                tile_list.append(tile)
                node_ids_to_tiles_reference[node_id] = tile_list

        ret = []
        for tile in page.object_list:
            ret.append(LabelBasedGraph.from_tile(tile, node_ids_to_tiles_reference, {}))

        response_data = {
            "results": ret,
            "total_count": paginator.count,
            "total_pages": paginator.num_pages,
            "page": page_number,
        }

        return JSONResponse(response_data)


class CardFromNodegroupIdView(APIBase):
    def get(self, request, nodegroupid):
        try:
            card = Card.objects.get(nodegroup_id=nodegroupid)
        except models.GraphModel.DoesNotExist:
            return JSONErrorResponse(status=HTTPStatus.NOT_FOUND)

        return JSONResponse(card)
