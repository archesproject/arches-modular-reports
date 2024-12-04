from http import HTTPStatus

from django.db.models import Prefetch
from django.http import Http404
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.generic import View

from arches.app.views.api import APIBase
from arches.app.models import models
from arches.app.utils.decorators import can_read_resource_instance
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
