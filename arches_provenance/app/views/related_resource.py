import logging
from django.utils.translation import gettext as _

from arches.app.models.resource import Resource
from arches.app.utils.response import JSONResponse
from arches.app.utils.string_utils import str_to_bool
from arches.app.views.resource import RelatedResourcesView

from arches_provenance.app.utils.resource_utils import get_related_resources

logger = logging.getLogger(__name__)


class ProvenanceRelatedResourcesView(RelatedResourcesView):

    def get(self, request, resourceid=None, include_rr_count=True):
        ret = {}

        paginate = str_to_bool(request.GET.get("paginate", "true"))  # default to true

        if paginate:
            return super().get(
                request=request,
                resourceid=resourceid,
                include_rr_count=include_rr_count,
            )
        else:
            lang = request.GET.get("lang", request.LANGUAGE_CODE)
            resourceinstance_graphid = request.GET.get("resourceinstance_graphid")
            resource = Resource.objects.get(pk=resourceid)
            ret = get_related_resources(
                self=resource,
                lang=lang,
                user=request.user,
                resourceinstance_graphid=resourceinstance_graphid,
                graphs=self.graphs,
                include_rr_count=False,
            )

        return JSONResponse(ret)
