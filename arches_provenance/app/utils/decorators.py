import functools

from django.core.exceptions import PermissionDenied

from arches.app.models import models
from arches.app.utils.permission_backend import PermissionBackend


def can_read_nodegroup(view_func):
    """
    Decorator to ensure that the user has read permissions for a specific NodeGroup.

    The decorated view must accept 'nodegroupid' as a keyword argument.
    """

    @functools.wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        nodegroup_id = kwargs.get("nodegroupid")
        nodegroup = models.NodeGroup.objects.get(pk=nodegroup_id)

        permission_backend = PermissionBackend()

        if permission_backend.has_perm(
            user_obj=request.user, perm="models.read_nodegroup", obj=nodegroup
        ):
            return view_func(request, *args, **kwargs)
        else:
            raise PermissionDenied

    return _wrapped_view
