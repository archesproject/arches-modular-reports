from django.views.generic import View

from arches.app.utils.response import JSONResponse
from arches_provenance.models import ReportConfig


class ProvenanceEditableReportConfigView(View):
    def get(self, request):
        """Just get first. But if there are multiple in the future,
        the vue component will need to know which one to request."""
        result = ReportConfig.objects.filter(
            graph__resourceinstance=request.GET.get("resourceId")
        ).first()
        return JSONResponse(result.config if result else {})
