from http import HTTPStatus

from django.utils.translation import gettext as _
from django.views.generic import View

from arches.app.utils.response import JSONErrorResponse, JSONResponse
from arches_provenance.models import ReportConfig


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
