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

import json
import logging
import uuid
from django.db import connection

from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.contrib.auth.models import User, Group
from django.forms.models import model_to_dict
from django.http import HttpResponseNotFound
from django.http import Http404
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.generic import View
from django.utils import translation

from arches.app.models import models
from arches.app.models.card import Card
from arches.app.models.graph import Graph
from arches.app.models.tile import Tile
from arches.app.models.resource import Resource, PublishedModelError
from arches.app.models.system_settings import settings
from arches.app.utils.activity_stream_jsonld import ActivityStreamCollection
from arches.app.utils.betterJSONSerializer import JSONSerializer, JSONDeserializer
from arches.app.utils.decorators import group_required
from arches.app.utils.decorators import can_edit_resource_instance
from arches.app.utils.decorators import can_read_resource_instance
from arches.app.utils.i18n import LanguageSynchronizer, localize_complex_input
from arches.app.utils.pagination import get_paginator
from arches.app.utils.permission_backend import (
    get_default_settable_permissions,
    user_is_resource_editor,
    user_is_resource_reviewer,
    user_can_delete_resource,
)
from arches.app.utils.response import JSONResponse, JSONErrorResponse
from arches.app.utils.string_utils import str_to_bool
from arches.app.search.search_engine_factory import SearchEngineFactory
from arches.app.search.mappings import RESOURCES_INDEX
from arches.app.views.base import BaseManagerView, MapBaseManagerView
from arches.app.views.concept import Concept
from arches.app.datatypes.datatypes import DataTypeFactory

from arches.app.models.models import ResourceInstance

import arches.app.utils.permission_backend as apb

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
