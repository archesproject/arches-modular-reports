import copy
import re

from arches.app.permissions.arches_permission_base import (
    get_nodegroups_by_perm_for_user_or_group,
)


def update_report_configuration_with_nodegroup_permissions(
    report_configuration_instance,
    report_nodegroup_ids_with_user_read_permission,
    report_nodegroup_ids_with_user_write_permission,
):
    copy_of_report_configuration = copy.deepcopy(report_configuration_instance.config)

    nodegroup_uuids_by_node_alias = {
        node.alias: node.nodegroup.pk
        for node in report_configuration_instance.graph.node_set.all()
        if node.nodegroup
    }

    def filter_node(node):
        if isinstance(node, dict):
            config = node.get("config", {})

            if isinstance(config, dict):
                nodegroup_alias = config.get("nodegroup_alias")
                nodegroup_id = nodegroup_uuids_by_node_alias.get(nodegroup_alias)

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

                for key in ["tabs", "sections", "components", "node_aliases"]:
                    if key in config:
                        filtered = filter_list(config[key])

                        config[key] = filtered

                        looks_like_data_section = "graph_slug" not in config
                        if not filtered and looks_like_data_section:
                            return None

                if descriptor := config.get("descriptor"):
                    config["descriptor"] = filter_descriptor(descriptor)

            if "components" in node:
                filtered = filter_list(node["components"])

                if not filtered:
                    return None

                node["components"] = filtered

            return node

        elif isinstance(node, list):
            return filter_list(node)

        elif isinstance(node, str):
            if (
                (maybe_uuid := nodegroup_uuids_by_node_alias.get(node))
                and maybe_uuid
                and maybe_uuid not in report_nodegroup_ids_with_user_read_permission
            ):
                return None
            else:
                return node

        else:
            return node

    def filter_list(items):
        filtered = []

        for child in items:
            result = filter_node(child)

            if result:
                filtered.append(result)

        return filtered

    def filter_descriptor(descriptor):
        substrings = extract_substrings(descriptor)
        filtered = filter_list(substrings)
        for forbidden in set(substrings) - set(filtered):
            descriptor = descriptor.replace(f"<{forbidden}>", "")
        return descriptor

    return filter_node(copy_of_report_configuration)


def update_report_configuration_for_nodegroup_permissions(
    report_configuration_instance, user
):
    graph_nodegroup_ids = {
        node.nodegroup.pk
        for node in report_configuration_instance.graph.node_set.all()
        if node.nodegroup
    }

    report_nodegroup_ids_with_user_read_permission = set()
    report_nodegroup_ids_with_user_write_permission = set()

    nodegroups_permissions = get_nodegroups_by_perm_for_user_or_group(
        user_or_group=user,
        perms=["models.read_nodegroup", "models.write_nodegroup"],
    )

    for nodegroup, permissions in nodegroups_permissions.items():
        if nodegroup.pk not in graph_nodegroup_ids:
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


def extract_substrings(template_string):
    pattern = r"<(.*?)>"
    substrings = re.findall(pattern, template_string)

    return substrings
