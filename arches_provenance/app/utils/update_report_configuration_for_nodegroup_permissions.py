import copy

from django.db import models

from arches.app.models.models import Node, NodeGroup
from arches.app.permissions.arches_permission_base import (
    get_nodegroups_by_perm_for_user_or_group,
)


def extract_nodegroup_ids_from_report_configuration(report_configuration_instance):
    nodegroup_aliases = set()

    def find_nodegroup_alias(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == "nodegroup_alias":
                    nodegroup_aliases.add(value)
                else:
                    find_nodegroup_alias(value)

        elif isinstance(obj, list):
            for item in obj:
                find_nodegroup_alias(item)

    find_nodegroup_alias(report_configuration_instance.config)

    return NodeGroup.objects.filter(
        node__graph=report_configuration_instance.graph,
        node__alias__in=nodegroup_aliases,
    ).values_list("pk", flat=True)


def update_report_configuration_with_nodegroup_permissions(
    report_configuration_instance,
    report_nodegroup_ids_with_user_read_permission,
    report_nodegroup_ids_with_user_write_permission,
):
    copy_of_report_configuration = copy.deepcopy(report_configuration_instance.config)

    nodegroup_uuids_by_alias = {
        node.alias: node.pk
        for node in Node.objects.filter(
            graph=report_configuration_instance.graph, nodegroup_id=models.F("pk")
        )
    }

    def filter_node(node):
        if isinstance(node, dict):
            config = node.get("config", {})

            if isinstance(config, dict):
                nodegroup_alias = config.get("nodegroup_alias")
                nodegroup_id = nodegroup_uuids_by_alias.get(nodegroup_alias)

                if (
                    nodegroup_id
                    and nodegroup_id
                    not in report_nodegroup_ids_with_user_read_permission
                ):
                    return None

                config["has_write_permission"] = (
                    nodegroup_id in report_nodegroup_ids_with_user_write_permission
                    if nodegroup_id
                    else False
                )

                for key in ["tabs", "sections", "components"]:
                    if key in config:
                        filtered = filter_list(config[key])

                        if not filtered:
                            return None

                        config[key] = filtered

            if "components" in node:
                filtered = filter_list(node["components"])

                if not filtered:
                    return None

                node["components"] = filtered

            return node

        elif isinstance(node, list):
            return filter_list(node)

        else:
            return node

    def filter_list(items):
        filtered = []

        for child in items:
            result = filter_node(child)

            if result:
                filtered.append(result)

        return filtered

    return filter_node(copy_of_report_configuration)


def update_report_configuration_for_nodegroup_permissions(
    report_configuration_instance, user
):
    report_nodegroup_ids = extract_nodegroup_ids_from_report_configuration(
        report_configuration_instance
    )

    report_nodegroup_ids_with_user_read_permission = set()
    report_nodegroup_ids_with_user_write_permission = set()

    nodegroups_permissions = get_nodegroups_by_perm_for_user_or_group(
        user_or_group=user,
        perms=["models.read_nodegroup", "models.write_nodegroup"],
    )

    for nodegroup, permissions in nodegroups_permissions.items():
        if nodegroup.pk not in report_nodegroup_ids:
            continue

        if not permissions:  # Empty set implies user has all permissions
            report_nodegroup_ids_with_user_read_permission.add(nodegroup.pk)
            report_nodegroup_ids_with_user_write_permission.add(nodegroup.pk)
            continue

        if "read_nodegroup" in permissions:
            report_nodegroup_ids_with_user_read_permission.add(nodegroup.pk)

        if "write_nodegroup" in permissions:
            report_nodegroup_ids_with_user_write_permission.add(nodegroup.pk)

    return update_report_configuration_with_nodegroup_permissions(
        report_configuration_instance=report_configuration_instance,
        report_nodegroup_ids_with_user_read_permission=report_nodegroup_ids_with_user_read_permission,
        report_nodegroup_ids_with_user_write_permission=report_nodegroup_ids_with_user_write_permission,
    )
