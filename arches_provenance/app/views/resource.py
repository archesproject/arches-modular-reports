"""
ARCHES - a program developed to inventory and manage immovable cultural heritage.
Copyright (C) 2013 J. Paul Getty Trust and World Monuments Fund

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

import logging
from django.http import Http404
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _

from arches.app.models import models

from arches.app.models.graph import Graph

from arches.app.models.resource import Resource
from arches.app.utils.decorators import can_read_resource_instance

from arches.app.views.base import MapBaseManagerView

from arches.app.models.models import ResourceInstance

logger = logging.getLogger(__name__)

@method_decorator(can_read_resource_instance, name="dispatch")
class ResourceReportView(MapBaseManagerView):
    def get(self, request, resourceid=None):
        resource = Resource.objects.only("graph_id").get(pk=resourceid)
        graph = Graph.objects.get(graphid=resource.graph_id)
        
        name_resource=ResourceInstance.objects.get(resourceinstanceid=str(resourceid)).name
        try:
            map_markers = models.MapMarker.objects.all()
            geocoding_providers = models.Geocoder.objects.all()
        except AttributeError:
            raise Http404(
                _("No active report template is available for this resource.")
            )

        context = self.get_context_data(
            main_script="views/resource/report",
            resourceid=resourceid,
            report_templates=models.ReportTemplate.objects.all(),
            card_components=models.CardComponent.objects.all(),
            widgets=models.Widget.objects.all(),
            map_markers=map_markers,
            geocoding_providers=geocoding_providers,
            graph_name=graph.name,
            name_resource=name_resource,
        )
        if graph.iconclass:
            context["nav"]["icon"] = graph.iconclass
        context["nav"]["title"] = graph.name
        context["nav"]["res_edit"] = True
        context["nav"]["print"] = True

        return render(request, "views/resource/report.htm", context)
