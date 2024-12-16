from arches.app.utils.label_based_graph_v2 import LabelBasedGraph, LabelBasedNode


class LabelBasedGraphWithBranchExport(LabelBasedGraph):
    """Override to avoid parent_tree still being None after checking parent_tile."""

    @classmethod
    def _build_graph(
        cls,
        input_node,
        input_tile,
        parent_tree,
        node_ids_to_tiles_reference,
        nodegroup_cardinality_reference,
        serialized_graph,
        datatype_factory,
        node_ids_to_serialized_nodes,
        edge_domain_node_ids_to_range_nodes,
    ):
        for associated_tile in node_ids_to_tiles_reference.get(
            input_node["nodeid"], [input_tile]
        ):
            parent_tile = associated_tile.parenttile

            if associated_tile == input_tile or parent_tile == input_tile:
                if (
                    cls.is_valid_semantic_node(
                        node=input_node,
                        tile=associated_tile,
                        node_ids_to_tiles_reference=node_ids_to_tiles_reference,
                        edge_domain_node_ids_to_range_nodes=edge_domain_node_ids_to_range_nodes,
                    )
                    or input_node["nodeid"] in associated_tile.data
                ):

                    label_based_node = LabelBasedNode(
                        name=input_node["name"],
                        node_id=input_node["nodeid"],
                        tile_id=str(associated_tile.pk),
                        value=cls._get_display_value(
                            tile=associated_tile,
                            serialized_node=input_node,
                            datatype_factory=datatype_factory,
                        ),
                        cardinality=nodegroup_cardinality_reference.get(
                            str(associated_tile.nodegroup_id)
                        ),
                    )

                    if not parent_tree:  # if top node and
                        # if not parent_tile:  # if not top node in separate card
                        parent_tree = label_based_node
                    else:
                        parent_tree.child_nodes.append(label_based_node)

                    for child_node in edge_domain_node_ids_to_range_nodes.get(
                        input_node["nodeid"], []
                    ):
                        cls._build_graph(
                            input_node=child_node,
                            input_tile=associated_tile,
                            parent_tree=label_based_node,
                            node_ids_to_tiles_reference=node_ids_to_tiles_reference,
                            nodegroup_cardinality_reference=nodegroup_cardinality_reference,
                            serialized_graph=serialized_graph,
                            datatype_factory=datatype_factory,
                            node_ids_to_serialized_nodes=node_ids_to_serialized_nodes,
                            edge_domain_node_ids_to_range_nodes=edge_domain_node_ids_to_range_nodes,
                        )

        return parent_tree
