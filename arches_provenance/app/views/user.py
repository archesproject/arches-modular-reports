from arches.app.utils.response import JSONResponse
from arches.app.utils.permission_backend import user_can_edit_resource
from arches.app.views.api import APIBase


class CheckUserCanEditResource(APIBase):
    def get(self, request, resource_instance_id):
        return JSONResponse(user_can_edit_resource(request.user, resource_instance_id))
