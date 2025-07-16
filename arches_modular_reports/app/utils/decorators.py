import functools

from django.core.exceptions import BadRequest, PermissionDenied
from django.db.models import Q
from arches.app.models import models
from arches.app.utils.permission_backend import PermissionBackend


def can_read_nodegroup(view_func):
    """
    Decorator to ensure that the user has read permissions for a specific NodeGroup.
    The decorated view must accept 'nodegroup_alias' and 'resourceid' as keyword args.

    The nodegroup_alias can be looked up against a related graph slug
    instead by providing `related_graph_slug` on request.GET.
    """

    @functools.wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        nodegroup_alias = kwargs.get("nodegroup_alias")
        resource_id = kwargs.get("resourceid")
        filters = Q(node__alias=nodegroup_alias)
        if request.method == "GET" and (
            related_graph_slug := request.GET.get("related_graph_slug", None)
        ):
            filters &= Q(node__graph__slug=related_graph_slug)
        else:
            filters &= Q(node__graph__resourceinstance=resource_id)
        nodegroup = models.NodeGroup.objects.get(filters)
        if not nodegroup:
            raise BadRequest

        permission_backend = PermissionBackend()

        # TODO: remove superuser check once `has_perm` is updated to handle superusers
        if request.user.is_superuser or permission_backend.has_perm(
            user_obj=request.user, perm="models.read_nodegroup", obj=nodegroup
        ):
            return view_func(request, *args, **kwargs)
        else:
            raise PermissionDenied

    return _wrapped_view
