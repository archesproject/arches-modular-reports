import functools

from django.core.exceptions import PermissionDenied, ObjectDoesNotExist

from arches.app.models import models


def user_can_read_nodegroup(view_func):
    """
    Decorator to ensure that the user has read permissions for a specific NodeGroup.

    The decorated view must accept 'nodegroupid' as a keyword argument.
    """

    @functools.wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        nodegroup_id = kwargs.get("nodegroupid")

        try:
            nodegroup = models.NodeGroup.objects.get(pk=nodegroup_id)
        except ObjectDoesNotExist:
            raise ValueError

        if request.user.has_perm("models.read_nodegroup", nodegroup):
            return view_func(request, *args, **kwargs)
        else:
            raise PermissionDenied

    return _wrapped_view
