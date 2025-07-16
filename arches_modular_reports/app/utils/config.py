def extract_nodegroup_aliases_and_graph_slugs(dict_or_list, accumulator=None):
    """Return a set of 2-element tuples: (nodegroup_alias, graph_slug)."""
    if not accumulator:
        accumulator = set()
    match dict_or_list:
        case list():
            for item in dict_or_list:
                accumulator = extract_nodegroup_aliases_and_graph_slugs(
                    item, accumulator
                )
        case dict():
            if (
                "nodegroup_alias" in dict_or_list
                and "related_graph_slug" in dict_or_list
            ):
                accumulator.add(
                    (
                        dict_or_list["nodegroup_alias"],
                        dict_or_list["related_graph_slug"],
                    )
                )
            for val in dict_or_list.values():
                accumulator = extract_nodegroup_aliases_and_graph_slugs(
                    val, accumulator
                )
        case _:
            return accumulator

    return accumulator
