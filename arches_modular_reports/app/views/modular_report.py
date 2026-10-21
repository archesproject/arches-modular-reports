import json
from http import HTTPStatus

from django.core.paginator import Paginator
from django.db.models import (
    Case,
    F,
    OuterRef,
    Q,
    Subquery,
    TextField,
    Value,
    When,
)
from django.db.models.fields.json import KT
from django.db.models.functions import Cast, Coalesce
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
from arches_modular_reports.app.utils.report_data_utils import EditValueDescriber
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
            for nodegroup_id in get_nodegroups_by_perm(
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
                    nodegroupid__in=models.CardModel.objects.annotate(
                        card_name_text=KT(f"name__{get_language()}"),
                        nodegroup_id_text=Cast("nodegroup_id", TextField()),
                    )
                    .filter(
                        graph__resourceinstance=resourceid,
                        card_name_text__icontains=query,
                    )
                    .values("nodegroup_id_text")
                )
            )
        if cursor := request.GET.get("after"):
            timestamp, editlogid = json.loads(cursor)
            edits = edits.filter(
                Q(timestamp__lt=timestamp)
                | Q(timestamp=timestamp, editlogid__lt=editlogid)
            )
        page_edits = list(edits[: self.page_size + 1])
        next_cursor = None
        if len(page_edits) > self.page_size:
            page_edits = page_edits[: self.page_size]
            next_cursor = json.dumps(
                [page_edits[-1].timestamp.isoformat(), str(page_edits[-1].editlogid)]
            )
        value_describer = EditValueDescriber(
            {edit.nodegroupid for edit in page_edits if edit.nodegroupid}
        )

        return JSONResponse(
            {
                "results": [
                    self.serialize_edit(edit, value_describer) for edit in page_edits
                ],
                "next_cursor": next_cursor,
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
            "edit_type": edit.edittype,
            "timestamp": edit.timestamp,
            "user": user_full_name or edit.user_username,
            "card_name": None,
            "values": [],
        }
        if edit.nodegroupid:
            serialized_edit["card_name"] = (
                value_describer.card_names_by_nodegroup_id.get(edit.nodegroupid, "")
            )
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
                | Q(
                    related_graph_id__in=models.GraphModel.objects.annotate(
                        graph_name_text=KT(f"name__{get_language()}")
                    )
                    .filter(
                        isresource=True,
                        source_identifier__isnull=True,
                        graph_name_text__icontains=query,
                    )
                    .values("pk")
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
                    relations, requested_graph, request.GET.get("after"), request.user
                )
            )

        graph_slugs = [
            graph_slug
            for graph_slug in request.GET.get("graphs", "").split(",")
            if graph_slug
        ]
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
                        relations, graphs_by_slug[graph_slug], None, request.user
                    )
                    for graph_slug in graph_slugs
                    if graph_slug in graphs_by_slug
                ]
            }
        )

    def serialize_group(self, relations, graph, cursor, user):
        group_relations = relations.filter(related_graph_id=graph.pk)
        if cursor is not None:
            sort_name, resourcexid = json.loads(cursor)
            if sort_name is None:
                group_relations = group_relations.filter(
                    related_resource_sort_name__isnull=True,
                    resourcexid__gt=resourcexid,
                )
            else:
                group_relations = group_relations.filter(
                    Q(related_resource_sort_name__gt=sort_name)
                    | Q(
                        related_resource_sort_name=sort_name,
                        resourcexid__gt=resourcexid,
                    )
                    | Q(related_resource_sort_name__isnull=True)
                )
        group_relations = group_relations.order_by(
            F("related_resource_sort_name").asc(nulls_last=True), "resourcexid"
        )

        page_relations = []
        has_more = False
        batch_start = 0
        while not has_more:
            batch = list(
                group_relations[batch_start : batch_start + self.page_size + 1]
            )
            readable_ids = readable_resource_ids(
                user, {relation.related_resource_id for relation in batch}
            )
            for relation in batch:
                if relation.related_resource_id not in readable_ids:
                    continue
                if len(page_relations) == self.page_size:
                    has_more = True
                    break
                page_relations.append(relation)
            if len(batch) <= self.page_size:
                break
            batch_start += len(batch)

        next_cursor = None
        if has_more:
            next_cursor = json.dumps(
                [
                    page_relations[-1].related_resource_sort_name,
                    str(page_relations[-1].resourcexid),
                ]
            )
        return {
            "graph_slug": graph.slug,
            "graph_name": str(graph.name),
            "iconclass": graph.iconclass,
            "color": graph.color,
            "next_cursor": next_cursor,
            "items": [
                {
                    "resourcexid": relation.resourcexid,
                    "display_name": str(relation.related_resource_name or ""),
                    "relationship": str(relation.relationship_label or ""),
                    "report_url": reverse(
                        "resource_report", args=[relation.related_resource_id]
                    ),
                }
                for relation in page_relations
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
    page_size = 25

    def get(self, request, resourceid):
        try:
            resource = models.ResourceInstance.objects.get(pk=resourceid)
        except models.ResourceInstance.DoesNotExist:
            return JSONErrorResponse(status=HTTPStatus.NOT_FOUND)
        readable_nodegroup_ids = {
            str(nodegroup_id)
            for nodegroup_id in get_nodegroups_by_perm(
                request.user, "models.read_nodegroup"
            )
        }
        requested_sources = []
        source_filter = Q()
        for source in request.GET.get("sources", "").split(","):
            graph_slug, _separator, node_alias = source.partition(":")
            requested_sources.append((graph_slug, node_alias))
            source_filter |= Q(graph__slug=graph_slug, alias=node_alias)
        file_nodes_by_source = {
            (file_node.graph.slug, file_node.alias): file_node
            for file_node in models.Node.objects.filter(
                source_filter,
                datatype="file-list",
                source_identifier__isnull=True,
                nodegroup_id__in=readable_nodegroup_ids,
            ).select_related("graph")
        }
        cursor = None
        if raw_cursor := request.GET.get("after"):
            cursor = json.loads(raw_cursor)

        images = []
        last_included_tile = None
        readable_by_resource_id = {resource.pk: True}
        for source_index, requested_source in enumerate(requested_sources):
            file_node = file_nodes_by_source.get(requested_source)
            if file_node is None or (cursor is not None and source_index < cursor[0]):
                continue
            tiles = self.ordered_tiles(resource, file_node, readable_nodegroup_ids)
            if cursor is not None and source_index == cursor[0]:
                _source_index, resource_id, sortorder, tileid = cursor
                tiles = tiles.filter(
                    Q(resourceinstance_id__gt=resource_id)
                    | Q(resourceinstance_id=resource_id, tile_sortorder__gt=sortorder)
                    | Q(
                        resourceinstance_id=resource_id,
                        tile_sortorder=sortorder,
                        tileid__gt=tileid,
                    )
                )
            for tile in self.readable_tiles(
                tiles, request.user, readable_by_resource_id
            ):
                tile_images = [
                    self.serialize_image(file_value, tile.resourceinstance)
                    for file_value in tile.data.get(str(file_node.pk)) or []
                    if file_value["type"].startswith("image/")
                ]
                if not tile_images:
                    continue
                if len(images) >= self.page_size:
                    return JSONResponse(
                        {
                            "images": images,
                            "next_cursor": json.dumps(last_included_tile),
                        }
                    )
                images.extend(tile_images)
                last_included_tile = [
                    source_index,
                    str(tile.resourceinstance_id),
                    tile.tile_sortorder,
                    str(tile.tileid),
                ]
        return JSONResponse({"images": images, "next_cursor": None})

    @staticmethod
    def ordered_tiles(resource, file_node, readable_nodegroup_ids):
        tiles = models.TileModel.objects.filter(nodegroup_id=file_node.nodegroup_id)
        if file_node.graph_id == resource.graph_id:
            tiles = tiles.filter(resourceinstance_id=resource.pk)
        else:
            readable_relations = models.ResourceXResource.objects.filter(
                node__nodegroup_id__in=readable_nodegroup_ids
            )
            tiles = tiles.filter(
                Q(
                    resourceinstance_id__in=readable_relations.filter(
                        from_resource_id=resource.pk,
                        to_resource_graph_id=file_node.graph_id,
                    ).values("to_resource_id")
                )
                | Q(
                    resourceinstance_id__in=readable_relations.filter(
                        to_resource_id=resource.pk,
                        from_resource_graph_id=file_node.graph_id,
                    ).values("from_resource_id")
                )
            )
        return (
            tiles.annotate(tile_sortorder=Coalesce("sortorder", 0))
            .select_related("resourceinstance")
            .order_by("resourceinstance_id", "tile_sortorder", "tileid")
        )

    def readable_tiles(self, tiles, user, readable_by_resource_id):
        batch_start = 0
        while True:
            batch = list(tiles[batch_start : batch_start + self.page_size + 1])
            unchecked_resource_ids = {
                tile.resourceinstance_id for tile in batch
            } - readable_by_resource_id.keys()
            readable_ids = readable_resource_ids(user, unchecked_resource_ids)
            for resource_id in unchecked_resource_ids:
                readable_by_resource_id[resource_id] = resource_id in readable_ids
            yield from (
                tile
                for tile in batch
                if readable_by_resource_id[tile.resourceinstance_id]
            )
            if len(batch) <= self.page_size:
                return
            batch_start += len(batch)

    @staticmethod
    def serialize_image(file_value, resource):
        language = get_language()
        resource_name = str(resource.name or "")
        caption = (
            file_value.get("title", {}).get(language, {}).get("value")
            or file_value.get("description", {}).get(language, {}).get("value")
            or resource_name
        )
        return {
            "url": file_value.get("url"),
            "caption": caption,
            "alt_text": file_value.get("altText", {}).get(language, {}).get("value")
            or caption,
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
