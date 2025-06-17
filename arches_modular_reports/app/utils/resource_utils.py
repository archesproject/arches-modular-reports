from uuid import UUID
from collections import defaultdict

from django.utils.translation import get_language
from django.utils.translation import gettext as _
from django.db.models import Count, F, Prefetch, Q
from django.forms.models import model_to_dict

from arches.app.models import models
from arches.app.models.system_settings import settings
from arches.app.utils import permission_backend
from arches.app.search.mappings import RESOURCES_INDEX
from arches.app.utils.i18n import rank_label
from arches.app.search.search_engine_factory import SearchEngineInstance as se
from arches.app.utils.permission_backend import get_filtered_instances


def get_related_resources(
    self,
    lang="en-US",
    limit=settings.RELATED_RESOURCES_EXPORT_LIMIT,
    start=0,
    page=0,
    user=None,
    resourceinstance_graphid=None,
    graphs=None,
    include_rr_count=True,
):
    """
    Returns an object that lists the related resources, the relationship types, and a reference to the current resource

    """

    # TODO This function is very similar to code in search results and the resource view. Needs to be centralized.
    def get_localized_descriptor(document, descriptor_type):
        language_codes = (get_language(), settings.LANGUAGE_CODE)
        descriptor = document["_source"][descriptor_type]
        result = descriptor[0] if len(descriptor) > 0 else {"value": _("Undefined")}
        for language_code in language_codes:
            for entry in descriptor:
                if entry["language"] == language_code and entry["value"] != "":
                    return entry["value"]
        return result["value"]

    if not graphs:
        graphs = list(
            models.GraphModel.objects.all()
            .exclude(pk=settings.SYSTEM_SETTINGS_RESOURCE_MODEL_ID)
            .exclude(isresource=False)
            .exclude(publication=None)
        )

    graph_lookup = {
        str(graph.graphid): {
            "name": graph.name,
            "iconclass": graph.iconclass,
            "fillColor": graph.color,
        }
        for graph in graphs
    }

    ret = {
        "resource_instance": self,
        "resource_relationships": [],
        "related_resources": [],
        "node_config_lookup": graph_lookup,
    }

    if page > 0:
        number_per_page = settings.RELATED_RESOURCES_PER_PAGE
        start = number_per_page * int(page - 1)
        limit = number_per_page * page

    def get_relations(
        resourceinstanceid,
        start,
        limit,
        resourceinstance_graphid=None,
    ):
        final_query = Q(resourceinstanceidfrom_id=resourceinstanceid) | Q(
            resourceinstanceidto_id=resourceinstanceid
        )

        if resourceinstance_graphid:
            to_graph_id_filter = Q(
                resourceinstancefrom_graphid_id=str(self.graph_id)
            ) & Q(resourceinstanceto_graphid_id=resourceinstance_graphid)
            from_graph_id_filter = Q(
                resourceinstancefrom_graphid_id=resourceinstance_graphid
            ) & Q(resourceinstanceto_graphid_id=str(self.graph_id))
            final_query = final_query & (to_graph_id_filter | from_graph_id_filter)

        return {  # resourceinstance_graphid = "00000000-886a-374a-94a5-984f10715e3a"
            "total": models.ResourceXResource.objects.filter(final_query).count(),
            "relations": models.ResourceXResource.objects.filter(final_query)[
                start:limit
            ],
        }

    resource_relations = get_relations(
        resourceinstanceid=self.resourceinstanceid,
        start=start,
        limit=limit,
        resourceinstance_graphid=resourceinstance_graphid,
    )

    ret["total"] = {"value": resource_relations["total"]}
    instanceids = set()

    readable_graphids = set(
        permission_backend.get_resource_types_by_perm(user, ["models.read_nodegroup"])
    )
    all_resource_ids = set()
    for relation in resource_relations["relations"]:
        all_resource_ids.add(str(relation.resourceinstanceidto_id))
        all_resource_ids.add(str(relation.resourceinstanceidfrom_id))
    exclusive_set, filtered_instances = get_filtered_instances(
        user, se, resources=list(all_resource_ids)
    )
    filtered_instances = filtered_instances if user is not None else []
    permitted_relation_dicts = []

    for relation in resource_relations["relations"]:
        relation = model_to_dict(relation)
        resourceid_to = relation["resourceinstanceidto"]
        resourceid_from = relation["resourceinstanceidfrom"]
        resourceinstanceto_graphid = relation["resourceinstanceto_graphid"]
        resourceinstancefrom_graphid = relation["resourceinstancefrom_graphid"]

        resourceid_to_permission = str(resourceid_to) not in filtered_instances
        resourceid_from_permission = str(resourceid_from) not in filtered_instances

        if exclusive_set:
            resourceid_to_permission = not (resourceid_to_permission)
            resourceid_from_permission = not (resourceid_from_permission)

        if (
            resourceid_to_permission
            and resourceid_from_permission
            and str(resourceinstanceto_graphid) in readable_graphids
            and str(resourceinstancefrom_graphid) in readable_graphids
        ):
            permitted_relation_dicts.append(relation)
        else:
            ret["total"]["value"] -= 1

    # Fetch pref labels for relationship types in bulk.
    relationship_types = {
        relation["relationshiptype"]
        for relation in permitted_relation_dicts
        if relation["relationshiptype"]
    }
    relationship_type_values = (
        models.Value.objects.filter(
            value__in=relationship_types,
        )
        .select_related("concept")
        .prefetch_related(
            Prefetch(
                "concept__value_set",
                # Begin with an order, so that if rank_label()
                # produces ties, we still have a deterministic result.
                queryset=models.Value.objects.order_by("pk"),
            ),
        )
    )
    preflabel_lookup = {
        str(rel_type.pk): (
            sorted(
                rel_type.concept.value_set.all(),
                key=lambda label: rank_label(
                    kind=label.valuetype_id,
                    source_lang=label.language_id,
                    target_lang=lang,
                ),
                reverse=True,
            )[0].value
            if rel_type.concept.value_set.all()
            else ""
        )
        for rel_type in relationship_type_values
    }

    for relation in permitted_relation_dicts:
        relation["relationshiptype_label"] = preflabel_lookup.get(
            relation["relationshiptype"], relation["relationshiptype"] or ""
        )

        ret["resource_relationships"].append(relation)
        instanceids.add(str(relation["resourceinstanceidto"]))
        instanceids.add(str(relation["resourceinstanceidfrom"]))

    if str(self.resourceinstanceid) in instanceids:
        instanceids.remove(str(self.resourceinstanceid))

    if len(instanceids) > 0:
        related_resources = se.search(index=RESOURCES_INDEX, id=list(instanceids))
        if related_resources:
            related_resource_ids = [
                resource["_id"]
                for resource in related_resources["docs"]
                if resource["found"]
            ]

            if include_rr_count:
                to_counts = (
                    models.ResourceXResource.objects.filter(
                        resourceinstanceidto__in=related_resource_ids
                    )
                    .values("resourceinstanceidto")
                    .annotate(to_count=Count("resourceinstanceidto"))
                    # ORDER BY NULLS LAST is necessary for "pipelined" GROUP BY, see
                    # https://use-the-index-luke.com/sql/sorting-grouping/indexed-group-by
                    .order_by(F("resourceinstanceidto").asc(nulls_last=True))
                )
                from_counts = (
                    models.ResourceXResource.objects.filter(
                        resourceinstanceidfrom__in=related_resource_ids
                    )
                    .values("resourceinstanceidfrom")
                    .annotate(from_count=Count("resourceinstanceidfrom"))
                    .order_by(F("resourceinstanceidfrom").asc(nulls_last=True))
                )

                total_relations_by_resource_id: dict[UUID:int] = defaultdict(int)
                for related_resource_count in to_counts:
                    total_relations_by_resource_id[
                        related_resource_count["resourceinstanceidto"]
                    ] += related_resource_count["to_count"]
                for related_resource_count in from_counts:
                    total_relations_by_resource_id[
                        related_resource_count["resourceinstanceidfrom"]
                    ] += related_resource_count["from_count"]

            for resource in related_resources["docs"]:
                if resource["found"]:
                    resource["_source"]["total_relations"] = {"value": "?"}
                    if include_rr_count:
                        resource["_source"]["total_relations"] = {
                            "value": total_relations_by_resource_id[
                                UUID(resource["_id"])
                            ]
                        }
                    for descriptor_type in ("displaydescription", "displayname"):
                        descriptor = get_localized_descriptor(resource, descriptor_type)
                        if descriptor:
                            resource["_source"][descriptor_type] = descriptor
                        else:
                            resource["_source"][descriptor_type] = _("Undefined")

                    ret["related_resources"].append(resource["_source"])

    return ret
