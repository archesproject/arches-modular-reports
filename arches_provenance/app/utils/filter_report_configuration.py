import copy

from arches.app.utils.permission_backend import get_nodegroups_by_perm


def extract_nodegroup_ids_from_report_configuration(data):
    nodegroup_ids = []

    def find_nodegroup_id(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == "nodegroup_id":
                    nodegroup_ids.append(value)
                else:
                    find_nodegroup_id(value)

        elif isinstance(obj, list):
            for item in obj:
                find_nodegroup_id(item)

    find_nodegroup_id(data)

    return nodegroup_ids


def filter_report_configuration_on_permitted_nodegroups(
    report_configuration, permitted_nodegroup_ids
):
    copy_of_report_configuration = copy.deepcopy(report_configuration)

    def filter_node(node):
        if isinstance(node, dict):
            config = node.get("config", {})

            if isinstance(config, dict):
                nodegroup_id = config.get("nodegroup_id")

                if nodegroup_id and nodegroup_id not in permitted_nodegroup_ids:
                    return None

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


def filter_report_configuration_for_nodegroup_permissions(report_configuration, user):
    nodegroup_ids = extract_nodegroup_ids_from_report_configuration(
        report_configuration
    )
    user_nodegroup_ids = set(
        str(nodegroup_id)
        for nodegroup_id in get_nodegroups_by_perm(user, ["models.read_nodegroup"])
    )

    return filter_report_configuration_on_permitted_nodegroups(
        report_configuration,
        set(
            nodegroup_id
            for nodegroup_id in nodegroup_ids
            if nodegroup_id in user_nodegroup_ids
        ),
    )
