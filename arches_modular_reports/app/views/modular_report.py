import json
from http import HTTPStatus

from django.core.paginator import Paginator
from django.db.models import Case, F, OuterRef, Q, Subquery, Value, When
from django.db.models.fields.json import KT
from django.http import Http404
from django.shortcuts import render
from django.urls import reverse
from django.utils import translation
from django.utils.decorators import method_decorator
from django.utils.translation import get_language, get_language_info, gettext as _
from django.views.generic import View

from arches.app.models import models
from arches.app.utils.betterJSONSerializer import JSONDeserializer
from arches.app.utils.decorators import can_read_resource_instance
from arches.app.utils.permission_backend import (
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
from arches.extensions.vue_components.utils.nodegroup_permissions import (
    nodegroup_ids_with_inherited_permission,
)

from arches_modular_reports.app.utils.decorators import can_read_nodegroup
from arches_modular_reports.app.utils.get_report_config import get_report_config
from arches_modular_reports.app.utils.report_data_utils import (
    EditValueDescriber,
    file_metadata_text,
    localized_text,
)
from arches_modular_reports.app.utils.nodegroup_tile_data_utils import (
    build_valueid_annotation,
    get_sorted_filtered_tiles,
)
from arches_modular_reports.app.utils.update_report_configuration_for_nodegroup_permissions import (
    update_report_configuration_for_nodegroup_permissions,
)
from arches_modular_reports.models import ReportConfig


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

        user_can_edit = user_can_edit_resource(request.user, resource=resource)

        return JSONResponse(
            {
                "graph": {
                    "name": str(resource.graph.name),
                    "slug": resource.graph.slug,
                    "iconclass": resource.graph.iconclass,
                },
                "lifecycle_state": resource.resource_instance_lifecycle_state.serialize(),
                "language": get_language(),
                "language_dir": (
                    "rtl" if get_language_info(get_language())["bidi"] else "ltr"
                ),
                "permissions": {
                    "can_edit": user_can_edit,
                    "can_delete": user_can_delete_resource(
                        request.user, resource=resource
                    ),
                    "can_copy": user_can_edit
                    and group_required(request.user, "Resource Editor"),
                    "is_reviewer": user_is_resource_reviewer(
                        request.user, resource=resource
                    ),
                },
            }
        )


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
            for nodegroup_id in nodegroup_ids_with_inherited_permission(
                request.user, "models.read_nodegroup"
            )
        }
        edits = (
            models.EditLog.objects.filter(resourceinstanceid=str(resourceid))
            .filter(
                Q(nodegroupid__isnull=True) | Q(nodegroupid__in=readable_nodegroup_ids)
            )
            .order_by("-timestamp", "-editlogid")
        )
        if query := request.GET.get("q", "").strip():
            edits = edits.filter(
                Q(user_firstname__icontains=query)
                | Q(user_lastname__icontains=query)
                | Q(user_username__icontains=query)
                | Q(
                    nodegroupid__in=self.nodegroup_ids_with_card_name(resourceid, query)
                )
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
    def nodegroup_ids_with_card_name(resourceid, query):
        graph_id = (
            models.ResourceInstance.objects.filter(pk=resourceid)
            .values_list("graph_id", flat=True)
            .first()
        )
        return [
            str(nodegroup_id)
            for nodegroup_id, card_name in models.CardModel.objects.filter(
                graph_id=graph_id
            ).values_list("nodegroup_id", "name")
            if query.casefold() in localized_text(card_name).casefold()
        ]

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
        permitted_nodegroup_ids = nodegroup_ids_with_inherited_permission(
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
                relationship_label=Case(
                    When(
                        relates_from_this_resource,
                        then=Subquery(
                            models.CardXNodeXWidget.objects.filter(
                                node=OuterRef("node")
                            ).values("label")[:1]
                        ),
                    ),
                    default=Value(None),
                ),
            )
            .annotate(
                related_resource_sort_name=KT(
                    f"related_resource_name__{get_language()}"
                ),
            )
        )
        if query := request.GET.get("q", "").strip():
            relations = relations.annotate(
                relationship_label_text=Subquery(
                    models.CardXNodeXWidget.objects.filter(
                        node=OuterRef("node")
                    ).values(label_text=KT(f"label__{get_language()}"))[:1]
                )
            ).filter(
                Q(related_resource_sort_name__icontains=query)
                | (
                    relates_from_this_resource
                    & Q(relationship_label_text__icontains=query)
                )
                | Q(related_graph_id__in=self.graph_ids_named(query))
            )
        relations = relations.filter(
            related_resource_id__in=readable_resource_ids(
                request.user,
                set(relations.values_list("related_resource_id", flat=True)),
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
                    relations,
                    requested_graph,
                    page_number=request.GET.get("page", 1),
                )
            )

        if requested_graph_slugs := request.GET.get("graphs"):
            graph_slugs = requested_graph_slugs.split(",")
            graphs_by_slug = {
                graph.slug: graph
                for graph in models.GraphModel.objects.filter(
                    slug__in=graph_slugs,
                    isresource=True,
                    source_identifier__isnull=True,
                )
            }
            return JSONResponse(
                {
                    "groups": [
                        self.serialize_group(
                            relations,
                            graphs_by_slug[graph_slug],
                            page_number=1,
                        )
                        for graph_slug in graph_slugs
                        if graph_slug in graphs_by_slug
                    ]
                }
            )
        return JSONResponse(
            {
                "groups": [
                    self.serialize_group(relations, graph, page_number=1)
                    for graph in sorted(
                        related_graphs, key=lambda graph: str(graph.name)
                    )
                ]
            }
        )

    @staticmethod
    def graph_ids_named(query):
        return [
            graph.pk
            for graph in models.GraphModel.objects.filter(
                isresource=True, source_identifier__isnull=True
            )
            if query.casefold() in str(graph.name).casefold()
        ]

    def serialize_group(self, relations, graph, page_number):
        group_relations = relations.filter(related_graph_id=graph.pk).order_by(
            F("related_resource_sort_name").asc(nulls_last=True), "resourcexid"
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
                    "resourcexid": relation.resourcexid,
                    "display_name": localized_text(relation.related_resource_name),
                    "relationship": localized_text(relation.relationship_label),
                    "report_url": reverse(
                        "resource_report", args=[relation.related_resource_id]
                    ),
                }
                for relation in relation_page
            ],
        }


def readable_resource_ids(user, resource_ids):
    return {
        resource.pk
        for resource in models.ResourceInstance.objects.filter(pk__in=resource_ids)
        if user_can_read_resource(user, resource=resource)
    }


@method_decorator(can_read_resource_instance, name="dispatch")
class ResourceImagesView(APIBase):
    def get(self, request, resourceid):
        try:
            resource = models.ResourceInstance.objects.get(pk=resourceid)
        except models.ResourceInstance.DoesNotExist:
            return JSONErrorResponse(status=HTTPStatus.NOT_FOUND)
        readable_nodegroup_ids = {
            str(nodegroup_id)
            for nodegroup_id in nodegroup_ids_with_inherited_permission(
                request.user, "models.read_nodegroup"
            )
        }
        images = []
        for source in request.GET.get("sources", "").split(","):
            graph_slug, _separator, node_alias = source.partition(":")
            file_node = models.Node.objects.filter(
                graph__slug=graph_slug,
                alias=node_alias,
                datatype="file-list",
                source_identifier__isnull=True,
            ).first()
            if (
                file_node is None
                or str(file_node.nodegroup_id) not in readable_nodegroup_ids
            ):
                continue
            if file_node.graph_id == resource.graph_id:
                resource_ids = {resource.pk}
            else:
                resource_ids = readable_resource_ids(
                    request.user,
                    self.related_resource_ids(
                        resource.pk, file_node.graph_id, readable_nodegroup_ids
                    ),
                )
            tiles = (
                models.TileModel.objects.filter(
                    resourceinstance_id__in=resource_ids,
                    nodegroup_id=file_node.nodegroup_id,
                )
                .select_related("resourceinstance")
                .order_by("resourceinstance_id", "sortorder", "tileid")
            )
            for tile in tiles:
                for file_value in tile.data.get(str(file_node.pk)) or []:
                    if str(file_value.get("type", "")).startswith("image/"):
                        images.append(
                            self.serialize_image(file_value, tile.resourceinstance)
                        )
        return JSONResponse({"images": images})

    @staticmethod
    def related_resource_ids(resource_id, graph_id, readable_nodegroup_ids):
        readable_relations = models.ResourceXResource.objects.filter(
            node__nodegroup_id__in=readable_nodegroup_ids
        )
        return set(
            readable_relations.filter(
                from_resource_id=resource_id, to_resource_graph_id=graph_id
            ).values_list("to_resource_id", flat=True)
        ) | set(
            readable_relations.filter(
                to_resource_id=resource_id, from_resource_graph_id=graph_id
            ).values_list("from_resource_id", flat=True)
        )

    @staticmethod
    def serialize_image(file_value, resource):
        resource_name = localized_text(resource.name)
        caption = (
            file_metadata_text(file_value, "title")
            or file_metadata_text(file_value, "description")
            or resource_name
        )
        return {
            "url": file_value.get("url"),
            "name": file_value.get("name"),
            "caption": caption,
            "alt_text": file_metadata_text(file_value, "altText") or caption,
            "resourceinstanceid": str(resource.pk),
            "resource_name": resource_name,
            "report_url": reverse("resource_report", args=[resource.pk]),
        }


class NodePresentationView(APIBase):
    @method_decorator(can_read_resource_instance, name="dispatch")
    def get(self, request, resourceid):
        try:
            graph = models.GraphModel.objects.filter(resourceinstance=resourceid).get()
        except models.GraphModel.DoesNotExist:
            return JSONErrorResponse(status=HTTPStatus.NOT_FOUND)
        permitted_nodegroups = nodegroup_ids_with_inherited_permission(
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
