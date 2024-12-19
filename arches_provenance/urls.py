import uuid
import json
import logging
from django.shortcuts import render
from django.urls import include, re_path, path
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.utils.decorators import method_decorator

from arches.app.views.base import BaseManagerView
from arches.app.models.graph import Graph
from arches.app.models.resource import Resource
from arches.app.models.system_settings import settings
from arches.app.utils.decorators import can_read_resource_instance
from arches.app.utils.data_management.resources.formats.rdffile import JsonLdWriter

from arches_provenance.app.views.provenance_report import provenance_report
from arches_provenance.app.views.provenance_report import ProvenanceSummaryTables
from arches_provenance.app.views.provenance_report import ProvenanceRelatedResources
from arches_provenance.app.views.provenance_report import ProvenanceGroupReportView
from arches_provenance.app.views.provenance_report import ProvenanceEditorView
from arches_provenance.app.views.provenance_report import ProvenanceSourceReferences
from arches_provenance.app.views.editable_report import (
    EditableReportAwareResourceReportView,
    NodePresentationView,
    ProvenanceEditableReportConfigView,
    NodegroupTileDataView,
    CardFromNodegroupIdView,
)

uuid_regex = settings.UUID_REGEX
logger = logging.getLogger(__name__)


@method_decorator(can_read_resource_instance, name="dispatch")
class GraphResourceReportView(BaseManagerView):

    def __init__(self, *args, **kwargs):
        super(GraphResourceReportView, self).__init__(*args, **kwargs)
        self.class_styles = {
            "HumanMadeObject": "object",
            "Place": "place",
            "Actor": "actor",
            "Person": "actor",
            "Group": "actor",
            "Type": "type",
            "MeasurementUnit": "type",
            "Currency": "type",
            "Material": "type",
            "Language": "type",
            "Name": "name",
            "Identifier": "name",
            "Dimension": "dims",
            "MonetaryAmount": "dims",
            "LinguisticObject": "infoobj",
            "VisualItem": "infoobj",
            "InformationObject": "infoobj",
            "Set": "infoobj",
            "PropositionalObject": "infoobj",
            "Right": "infoobj",
            "PropertyInterest": "infoobj",
            "TimeSpan": "timespan",
            "Activity": "event",
            "Event": "event",
            "Birth": "event",
            "Death": "event",
            "Production": "event",
            "Destruction": "event",
            "Creation": "event",
            "Formation": "event",
            "Dissolution": "event",
            "Acquisition": "event",
            "TransferOfCustody": "event",
            "Move": "event",
            "Payment": "event",
            "AttributeAssignment": "event",
            "Phase": "event",
            "Relationship": "dims",
            "RightAcquisition": "event",
            "PartRemoval": "event",
            "PartAddition": "event",
            "Encounter": "event",
        }

    def uri_to_label_link(self, uri, curr_int=0):
        link = ""
        if uri.startswith("http://vocab.getty.edu/"):
            link = uri
            uri = uri.replace("http://vocab.getty.edu/", "")
            uri = uri.replace("/", ":")
        elif uri.startswith("http://localhost:8000/resources/"):
            uri = uri.replace("http://localhost:8000/resources/", "")
            link = f"http://localhost:8000/graph_report/{uri}"
        elif uri.startswith("http://localhost:8000/tile/"):
            uri = f"_:b{curr_int}"
        elif uri.startswith("http://qudt.org/1.1/vocab/unit/"):
            uri = uri.replace("http://qudt.org/1.1/vocab/unit/", "qudt:")
        else:
            # print("Unhandled URI: %s" % uri)
            pass
        return uri, link

    def walk(self, js, curr_int, id_map, mermaid):
        if isinstance(js, dict):
            # Resource
            curr = js.get("id", str(uuid.uuid4()))
            if curr in id_map:
                currid = id_map[curr]
            else:
                currid = "O%s" % curr_int
                curr_int += 1
                id_map[curr] = currid
            lbl, link = self.uri_to_label_link(curr, curr_int)
            line = "%s(%s)" % (currid, lbl)
            if not line in mermaid:
                mermaid.append(line)
            if link:
                line = f'click {currid} "{link}" "Link"'
                if not line in mermaid:
                    mermaid.append(line)
            t = js.get("type", "")
            if t:
                style = self.class_styles.get(t, "")
                if style:
                    line = "class %s %s;" % (currid, style)
                    if not line in mermaid:
                        mermaid.append("class %s %s;" % (currid, style))
                else:
                    print("No style for class %s" % t)
                line = "%s-- type -->%s_0[%s]" % (currid, currid, t)
                if not line in mermaid:
                    mermaid.append(line)
                    mermaid.append("class %s_0 classstyle;" % currid)

            n = 0
            for k, v in js.items():
                n += 1
                if k in ["@context", "id", "type"]:
                    continue
                elif isinstance(v, list):
                    for vi in v:
                        if isinstance(vi, dict):
                            (rng, curr_int, id_map) = self.walk(
                                vi, curr_int, id_map, mermaid
                            )
                            mermaid.append("%s-- %s -->%s" % (currid, k, rng))
                        else:
                            print("Iterating a list and found %r" % vi)
                elif isinstance(v, dict):
                    (rng, curr_int, id_map) = self.walk(v, curr_int, id_map, mermaid)
                    line = "%s-- %s -->%s" % (currid, k, rng)
                    if not line in mermaid:
                        mermaid.append(line)
                else:
                    if type(v) in [str, bytes]:
                        # :|
                        v = v.replace('"', "#quot;")
                        if len(v) > 80:
                            v = v[:80] + "..."
                        v = "\"''%s''\"" % v
                    line = "%s-- %s -->%s_%s(%s)" % (currid, k, currid, n, v)
                    if not line in mermaid:
                        mermaid.append(line)
                        mermaid.append("class %s_%s literal;" % (currid, n))
            return (currid, curr_int, id_map)

    def build_mermaid(self, js):
        curr_int = 1
        mermaid = []
        id_map = {}
        mermaid.append("graph TD")
        mermaid.append("classDef object stroke:black,fill:#E1BA9C,rx:20px,ry:20px;")
        mermaid.append("classDef actor stroke:black,fill:#FFBDCA,rx:20px,ry:20px;")
        mermaid.append("classDef type stroke:red,fill:#FAB565,rx:20px,ry:20px;")
        mermaid.append("classDef name stroke:orange,fill:#FEF3BA,rx:20px,ry:20px;")
        mermaid.append("classDef dims stroke:black,fill:#c6c6c6,rx:20px,ry:20px;")
        mermaid.append("classDef infoobj stroke:#907010,fill:#fffa40,rx:20px,ry:20px")
        mermaid.append("classDef timespan stroke:blue,fill:#ddfffe,rx:20px,ry:20px")
        mermaid.append("classDef place stroke:#3a7a3a,fill:#aff090,rx:20px,ry:20px")
        mermaid.append("classDef event stroke:blue,fill:#96e0f6,rx:20px,ry:20px")
        mermaid.append("classDef literal stroke:black,fill:#f0f0e0;")
        mermaid.append("classDef classstyle stroke:black,fill:white;")
        self.walk(js, curr_int, id_map, mermaid)
        return "\n".join(mermaid)

    def get(self, request, resourceid=None):

        resource = Resource.objects.get(pk=resourceid)
        graph = Graph.objects.get(graphid=resource.graph_id)
        writer = JsonLdWriter()
        js = writer.build_json(resourceinstanceids=[resourceid])

        # Now apply mermaid algorithm to the json-ld
        mmd = self.build_mermaid(js)

        displayname = resource.displayname

        context = self.get_context_data(
            main_script="views/resource",
            displayname=displayname,
            data=mmd,
            mmid=resourceid,
            jsonld=json.dumps(js, indent=2),
        )
        context["nav"]["title"] = displayname
        if graph.iconclass:
            context["nav"]["icon"] = graph.iconclass

        return render(request, "views/resource/graph_report.htm", context)


urlpatterns = [
    # re_path(r'^', include('arches.urls')),
    re_path(
        r"^graph_report/(?P<resourceid>%s|())$" % uuid_regex,
        GraphResourceReportView.as_view(),
        name="resource_graph_report",
    ),
    re_path(
        r"^provenance_report$", provenance_report.as_view(), name="provenance_report"
    ),
    re_path(
        r"^provenance_summary_table$",
        ProvenanceSummaryTables.as_view(),
        name="provenance_summary_table",
    ),
    re_path(
        r"^provenance_source_references$",
        ProvenanceSourceReferences.as_view(),
        name="provenance_source_references",
    ),
    re_path(
        r"^provenance_related_resources$",
        ProvenanceRelatedResources.as_view(),
        name="provenance_related_resources",
    ),
    re_path(
        r"^provenance_editor$", ProvenanceEditorView.as_view(), name="provenance_editor"
    ),
    path(
        "provenance_editable_report_config",
        ProvenanceEditableReportConfigView.as_view(),
        name="provenance_editable_report_config",
    ),
    # Override core arches resource report view to allow rendering
    # distinct template for editable reports.
    re_path(
        r"^report/(?P<resourceid>%s)$" % uuid_regex,
        EditableReportAwareResourceReportView.as_view(),
        name="resource_report",
    ),
    path(
        "api/node_presentation/<uuid:resourceid>",
        NodePresentationView.as_view(),
        name="api_node_presentation",
    ),
    path(
        "api/nodegroup_tile_data/<uuid:resourceinstanceid>/<uuid:nodegroupid>",
        NodegroupTileDataView.as_view(),
        name="api_nodegroup_tile_data",
    ),
    path(
        "api/card_from_nodegroup_id/<uuid:nodegroupid>",
        CardFromNodegroupIdView.as_view(),
        name="api_card_from_nodegroup_id",
    ),
]

try:
    import arches_health

    urlpatterns = urlpatterns + [re_path(r"^ht/", include("health_check.urls"))]
    urlpatterns = urlpatterns + [re_path(r"^ht-pub/", include("arches_health.urls"))]
    logger.info("loaded optional health check urls")
except Exception as e:
    logger.error(e)
    pass

# Ensure Arches core urls are superseded by project-level urls
urlpatterns.append(path("", include("arches.urls")))

# Adds URL pattern to serve media files during development
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Only handle i18n routing in active project. This will still handle the routes provided by Arches core and Arches applications,
# but handling i18n routes in multiple places causes application errors.
if settings.ROOT_URLCONF == __name__:
    if settings.SHOW_LANGUAGE_SWITCH is True:
        urlpatterns = i18n_patterns(*urlpatterns)

    urlpatterns.append(path("i18n/", include("django.conf.urls.i18n")))
