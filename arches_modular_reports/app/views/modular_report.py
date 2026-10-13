import json
from http import HTTPStatus

from django.core.paginator import Paginator
from django.db.models import Case, F, OuterRef, Q, Subquery, When
from django.db.models.fields.json import KT
from django.http import Http404
from django.shortcuts import render
from django.urls import reverse
from django.utils import translation
from django.utils.decorators import method_decorator
from django.utils.translation import get_language, get_language_info, gettext as _
from django.views.generic import View

from arches.app.datatypes.datatypes import DataTypeFactory
from arches.app.models import models
from arches.app.utils.betterJSONSerializer import JSONDeserializer
from arches.app.utils.decorators import can_read_resource_instance
from arches.app.utils.permission_backend import (
    get_nodegroups_by_perm,
    group_required,
    user_can_delete_resource,
    user_can_edit_resource,
    user_can_read_resource,
    user_is_resource_reviewer,
)
from arches.app.utils.response import JSONErrorResponse, JSONResponse
from arches.app.views.api import APIBase
from arches.app.views.base import MapBaseManagerView
from arches.app.views.resource import ResourceReportView

from arches_modular_reports.app.utils.decorators import can_read_nodegroup
from arches_modular_reports.app.utils.get_report_config import get_report_config
from arches_modular_reports.app.utils.nodegroup_tile_data_utils import (
    build_valueid_annotation,
    get_sorted_filtered_tiles,
)
from arches_modular_reports.app.utils.update_report_configuration_for_nodegroup_permissions import (
    update_report_configuration_for_nodegroup_permissions,
)
from arches_modular_reports.models import ReportConfig
from arches_modular_reports.resource_report import GEOMETRY_DATATYPE


def localized_text(i18n_value):
    if isinstance(i18n_value, dict):
        active_language_text = i18n_value.get(get_language())
        if active_language_text:
            return active_language_text
        populated_texts = [text for text in i18n_value.values() if text]
        if populated_texts:
            return populated_texts[0]
        return ""
    if i18n_value is None:
        return ""
    return str(i18n_value)


class GraphSlugFromIdView(APIBase):
    def get(self, request, graphid):
        try:
            graph = models.GraphModel.objects.values_list("slug", flat=True).get(
                pk=graphid
            )
        except models.GraphModel.DoesNotExist:
            return JSONErrorResponse(status=HTTPStatus.NOT_FOUND)

        return JSONResponse({"graph_slug": graph})


@method_decorator(can_read_resource_instance, name="dispatch")
class ModularReportConfigView(View):
    def get(self, request):
        try:
            resourceid = request.GET.get("resourceId")
            report_config_slug = request.GET.get("report_config_slug", "default")
            config_instance = get_report_config(resourceid, report_config_slug)
        except ReportConfig.DoesNotExist:
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
    def get(self, request, resourceid=None, report_config_slug="default"):
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
            try:
                config_instance = get_report_config(resourceid, report_config_slug)
                report_theme = config_instance.config.get("theme", None)
            except ReportConfig.DoesNotExist:
                return JSONErrorResponse(
                    _("No report config found."), status=HTTPStatus.NOT_FOUND
                )
            except:
                report_theme = None

            template = "views/resource/modular_report.htm"
            # Skip a few queries by jumping over the MapBaseManagerView
            # and calling its parent. This report doesn't use a map.
            context = super(MapBaseManagerView, self).get_context_data(
                main_script="views/resource/report",
                resourceid=resourceid,
                templateid=graph.template.pk,
                graph_slug=graph.slug,
                report_theme=report_theme,
                # To the extent possible, avoid DB queries needed for KO
                report_templates=[graph.template],
                report_config_slug=report_config_slug,
                card_components=models.CardComponent.objects.none(),
                widgets=models.Widget.objects.none(),
                map_markers=models.MapMarker.objects.none(),
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
class ReportContextView(APIBase):
    def get(self, request, resourceid):
        try:
            resource = models.ResourceInstance.objects.select_related(
                "graph", "resource_instance_lifecycle_state"
            ).get(pk=resourceid)
        except models.ResourceInstance.DoesNotExist:
            return JSONErrorResponse(status=HTTPStatus.NOT_FOUND)

        user_can_edit = user_can_edit_resource(request.user, resourceid=resourceid)

        return JSONResponse(
            {
                "graph": {
                    "name": str(resource.graph.name),
                    "slug": resource.graph.slug,
                    "iconclass": resource.graph.iconclass,
                    "color": resource.graph.color,
                },
                "lifecycle_state": resource.resource_instance_lifecycle_state.serialize(),
                "language": get_language(),
                "language_dir": (
                    "rtl" if get_language_info(get_language())["bidi"] else "ltr"
                ),
                "permissions": {
                    "can_edit": user_can_edit,
                    "can_delete": user_can_delete_resource(
                        request.user, resourceid=resourceid
                    ),
                    "can_copy": user_can_edit
                    and group_required(request.user, "Resource Editor"),
                    "is_reviewer": user_is_resource_reviewer(request.user),
                    "is_rdm_admin": group_required(request.user, "RDM Administrator"),
                },
            }
        )


class EditValueDescriber:
    def __init__(self):
        self.datatype_factory = DataTypeFactory()
        self.nodes_by_nodegroup_id = {}
        self.card_names_by_nodegroup_id = {}

    def card_name(self, nodegroup_id):
        if nodegroup_id not in self.card_names_by_nodegroup_id:
            card_name = (
                models.CardModel.objects.filter(nodegroup_id=nodegroup_id)
                .values_list("name", flat=True)
                .first()
            )
            self.card_names_by_nodegroup_id[nodegroup_id] = localized_text(card_name)
        return self.card_names_by_nodegroup_id[nodegroup_id]

    def nodes(self, nodegroup_id):
        if nodegroup_id not in self.nodes_by_nodegroup_id:
            nodegroup_nodes = list(
                models.Node.objects.filter(nodegroup_id=nodegroup_id)
                .exclude(datatype__in={"semantic", GEOMETRY_DATATYPE})
                .prefetch_related("cardxnodexwidget_set")
                .order_by("cardxnodexwidget__sortorder")
            )
            for node in nodegroup_nodes:
                widgets = node.cardxnodexwidget_set.all()
                widget_label = localized_text(widgets[0].label) if widgets else ""
                node.report_label = widget_label or node.name
            self.nodes_by_nodegroup_id[nodegroup_id] = nodegroup_nodes
        return self.nodes_by_nodegroup_id[nodegroup_id]

    def display_value(self, tile_data, nodegroup_id, node):
        raw_value = tile_data.get(str(node.pk))
        if raw_value in (None, "", [], {}):
            return ""
        tile = models.TileModel(nodegroup_id=nodegroup_id, data=tile_data)
        datatype = self.datatype_factory.get_instance(node.datatype)
        try:
            return datatype.get_display_value(tile, node)
        except (AttributeError, KeyError, TypeError, ValueError):
            return str(raw_value)

    def describe(self, edit):
        old_tile_data = edit.oldvalue if isinstance(edit.oldvalue, dict) else None
        new_tile_data = edit.newvalue if isinstance(edit.newvalue, dict) else None
        described_values = []
        for node in self.nodes(edit.nodegroupid):
            before = None
            after = None
            if old_tile_data is not None:
                before = self.display_value(old_tile_data, edit.nodegroupid, node)
            if new_tile_data is not None:
                after = self.display_value(new_tile_data, edit.nodegroupid, node)
            old_raw_value = (old_tile_data or {}).get(str(node.pk))
            new_raw_value = (new_tile_data or {}).get(str(node.pk))
            described_values.append(
                {
                    "node_alias": node.alias,
                    "label": node.report_label,
                    "before": before,
                    "after": after,
                    "changed": old_raw_value != new_raw_value,
                }
            )
        return described_values


@method_decorator(can_read_resource_instance, name="dispatch")
class EditHistoryView(APIBase):
    page_size = 25

    def get(self, request, resourceid):
        if not user_can_edit_resource(request.user, resourceid=resourceid):
            return JSONErrorResponse(
                _("Permission Denied"), status=HTTPStatus.FORBIDDEN
            )

        readable_nodegroup_ids = {
            str(nodegroup_id)
            for nodegroup_id in get_nodegroups_by_perm(
                request.user, "models.read_nodegroup"
            )
        }
        edits = (
            models.EditLog.objects.filter(resourceinstanceid=str(resourceid))
            .filter(
                Q(nodegroupid__isnull=True) | Q(nodegroupid__in=readable_nodegroup_ids)
            )
            .order_by("-timestamp")
        )
        paginator = Paginator(edits, self.page_size)
        edit_page = paginator.get_page(request.GET.get("page", 1))
        value_describer = EditValueDescriber()

        return JSONResponse(
            {
                "results": [
                    self.serialize_edit(edit, value_describer) for edit in edit_page
                ],
                "page": edit_page.number,
                "total_count": paginator.count,
                "has_next": edit_page.has_next(),
            }
        )

    @staticmethod
    def serialize_edit(edit, value_describer):
        user_full_name = " ".join(
            name_part
            for name_part in (edit.user_firstname, edit.user_lastname)
            if name_part
        )
        serialized_edit = {
            "editlogid": edit.editlogid,
            "transactionid": edit.transactionid,
            "edit_type": edit.edittype,
            "timestamp": edit.timestamp,
            "user": user_full_name or edit.user_username,
            "note": edit.note,
            "nodegroup_id": edit.nodegroupid,
            "tileid": edit.tileinstanceid,
            "card_name": None,
            "values": [],
        }
        if edit.nodegroupid:
            serialized_edit["card_name"] = value_describer.card_name(edit.nodegroupid)
            serialized_edit["values"] = value_describer.describe(edit)
        return serialized_edit


@method_decorator(can_read_resource_instance, name="dispatch")
class RelatedResourceGroupsView(APIBase):
    page_size = 25

    def get(self, request, resourceid):
        permitted_nodegroup_ids = get_nodegroups_by_perm(
            request.user, "models.read_nodegroup"
        )
        relates_from_this_resource = Q(from_resource_id=resourceid)
        relations = (
            models.ResourceXResource.objects.filter(
                Q(from_resource_id=resourceid) | Q(to_resource_id=resourceid),
                node__nodegroup_id__in=permitted_nodegroup_ids,
            )
            .annotate(
                related_resource_id=Case(
                    When(relates_from_this_resource, then=F("to_resource_id")),
                    default=F("from_resource_id"),
                ),
                related_graph_id=Case(
                    When(relates_from_this_resource, then=F("to_resource_graph_id")),
                    default=F("from_resource_graph_id"),
                ),
                related_resource_name=Case(
                    When(relates_from_this_resource, then=F("to_resource__name")),
                    default=F("from_resource__name"),
                ),
                relationship_label=Subquery(
                    models.CardXNodeXWidget.objects.filter(
                        node=OuterRef("node")
                    ).values("label")[:1]
                ),
            )
            .annotate(
                related_resource_sort_name=KT(
                    f"related_resource_name__{get_language()}"
                )
            )
        )
        related_graphs = models.GraphModel.objects.filter(
            pk__in=relations.values("related_graph_id")
        )

        if requested_graph_slug := request.GET.get("graph"):
            requested_graph = related_graphs.filter(slug=requested_graph_slug).first()
            if not requested_graph:
                return JSONErrorResponse(status=HTTPStatus.NOT_FOUND)
            return JSONResponse(
                self.serialize_group(
                    request,
                    relations,
                    requested_graph,
                    page_number=request.GET.get("page", 1),
                )
            )

        return JSONResponse(
            {
                "groups": [
                    self.serialize_group(request, relations, graph, page_number=1)
                    for graph in sorted(
                        related_graphs, key=lambda graph: str(graph.name)
                    )
                ]
            }
        )

    def serialize_group(self, request, relations, graph, page_number):
        group_relations = relations.filter(related_graph_id=graph.pk).order_by(
            F("related_resource_sort_name").asc(nulls_last=True)
        )
        paginator = Paginator(group_relations, self.page_size)
        relation_page = paginator.get_page(page_number)
        return {
            "graph_slug": graph.slug,
            "graph_name": str(graph.name),
            "iconclass": graph.iconclass,
            "color": graph.color,
            "total_count": paginator.count,
            "page": relation_page.number,
            "has_next": relation_page.has_next(),
            "items": [
                {
                    "resourceinstanceid": relation.related_resource_id,
                    "display_name": localized_text(relation.related_resource_name),
                    "relationship": localized_text(relation.relationship_label),
                    "report_url": reverse(
                        "resource_report", args=[relation.related_resource_id]
                    ),
                }
                for relation in relation_page
                if user_can_read_resource(
                    request.user, resourceid=relation.related_resource_id
                )
            ],
        }


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
        writable_nodegroup_ids = set(
            get_nodegroups_by_perm(request.user, "models.write_nodegroup")
        )
        nodes = list(
            models.Node.objects.filter(graph=graph)
            .filter(nodegroup__in=permitted_nodegroups)
            .select_related("nodegroup")
            .prefetch_related(
                "nodegroup__cardmodel_set",
                "cardxnodexwidget_set__widget",
            )
        )
        grouping_node_aliases_by_nodegroup_id = {
            node.nodegroup_id: node.alias
            for node in nodes
            if node.pk == node.nodegroup_id
        }

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
                    "datatype": node.datatype,
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
                    "card_visible": getattr_from_queryset(
                        node.nodegroup.cardmodel_set.all(),
                        "visible",
                        True,
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
                        "alias": grouping_node_aliases_by_nodegroup_id.get(
                            node.nodegroup_id
                        ),
                        "parent_nodegroup_id": node.nodegroup.parentnodegroup_id,
                        "writable": node.nodegroup_id in writable_nodegroup_ids,
                    },
                    "is_rich_text": get_widget_name(
                        node.cardxnodexwidget_set.all(), None
                    )
                    == "rich-text-widget",
                    "is_required": node.isrequired,
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
