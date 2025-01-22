import copy
import uuid

from arches.app.permissions.arches_permission_base import (
    get_nodegroups_by_perm_for_user_or_group,
)


def extract_nodegroup_ids_from_report_configuration(data):
    nodegroup_ids = set()

    def find_nodegroup_id(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == "nodegroup_id":
                    nodegroup_ids.add(uuid.UUID(value))
                else:
                    find_nodegroup_id(value)

        elif isinstance(obj, list):
            for item in obj:
                find_nodegroup_id(item)

    find_nodegroup_id(data)

    return nodegroup_ids


def update_report_configuration_with_nodegroup_permissions(
    report_configuration,
    report_nodegroup_ids_with_user_read_permission,
    report_nodegroup_ids_with_user_write_permission,
):
    copy_of_report_configuration = copy.deepcopy(report_configuration)

    def filter_node(node):
        if isinstance(node, dict):
            config = node.get("config", {})

            if isinstance(config, dict):
                nodegroup_id_string = config.get("nodegroup_id")
                nodegroup_id = (
                    uuid.UUID(nodegroup_id_string) if nodegroup_id_string else None
                )

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


def update_report_configuration_for_nodegroup_permissions(report_configuration, user):
    report_nodegroup_ids = extract_nodegroup_ids_from_report_configuration(
        report_configuration
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
        report_configuration=report_configuration,
        report_nodegroup_ids_with_user_read_permission=report_nodegroup_ids_with_user_read_permission,
        report_nodegroup_ids_with_user_write_permission=report_nodegroup_ids_with_user_write_permission,
    )
