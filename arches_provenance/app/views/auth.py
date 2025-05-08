from arches.app.views.auth import LoginView
from arches.app.models.system_settings import settings

# This file can be removed once #12034 from arches is merged
# and the arches version is updated in arches_provenance
# This file is a temporary workaround to fix the login process
# in the provenance app


class ProvenanceLoginView(LoginView):
    def get(self, request):
        """
        Override the get method to handle the login process.
        """
        request_copy = request.GET.copy()
        request_copy["next"] = request.GET.get("next", settings.LOGIN_REDIRECT_URL)
        request.GET = request_copy
        # Call the parent class's get method to handle the login process
        return super().get(request)

    def post(self, request):
        """
        Override the get method to handle the login process.
        """
        # import ipdb; ipdb.sset_trace()

        request_copy = request.POST.copy()
        request_copy["next"] = request.POST.get("next", settings.LOGIN_REDIRECT_URL)
        request.POST = request_copy
        # Call the parent class's get method to handle the login process
        return super().post(request)
