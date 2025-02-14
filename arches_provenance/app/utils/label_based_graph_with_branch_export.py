from functools import partial

from arches.app.models import models
from arches.app.utils.label_based_graph_v2 import (
    LabelBasedGraph,
    LabelBasedNode,
    NODE_ID_KEY,
    TILE_ID_KEY,
    NON_DATA_COLLECTING_NODE,
)


class LabelBasedGraphWithBranchExport(LabelBasedGraph):
    """
    Override to:
    1. avoid parent_tree still being None after checking parent_tile (override _build_graph())
    2. avoid N+1 queries for Card instances (override as_json())
    """

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

        # This checks card visibility.
        parent_tree.as_json = partial(cls.as_json, parent_tree)

        return parent_tree

    def as_json(
        self, compact=False, include_empty_nodes=True, include_hidden_nodes=True
    ):
        display_data = {}

        if not include_hidden_nodes:
            card = models.CardModel.objects.filter(nodegroup_id=self.node_id).first()
            try:
                if not card.visible:
                    return None
            except AttributeError:
                pass

        for child_node in self.child_nodes:
            formatted_node = child_node.as_json(
                compact=compact,
                include_empty_nodes=include_empty_nodes,
                include_hidden_nodes=include_hidden_nodes,
            )
            if formatted_node is not None:
                formatted_node_name, formatted_node_value = formatted_node.popitem()

                if include_empty_nodes or not child_node.is_empty():
                    previous_val = display_data.get(formatted_node_name)
                    cardinality = child_node.cardinality

                    # let's handle multiple identical node names
                    if not previous_val:
                        should_create_new_array = (
                            cardinality == "n" and self.tile_id != child_node.tile_id
                        )
                        display_data[formatted_node_name] = (
                            [formatted_node_value]
                            if should_create_new_array
                            else formatted_node_value
                        )
                    elif isinstance(previous_val, list):
                        display_data[formatted_node_name].append(formatted_node_value)
                    else:
                        display_data[formatted_node_name] = [
                            previous_val,
                            formatted_node_value,
                        ]

        val = self.value
        if compact and display_data:
            if self.value is not NON_DATA_COLLECTING_NODE:
                if self.value is not None:
                    display_data.update(self.value)
        elif compact and not display_data:  # if compact and no child nodes
            display_data = self.value
        elif not compact:
            display_data[NODE_ID_KEY] = self.node_id
            display_data[TILE_ID_KEY] = self.tile_id
            if self.value is not None and self.value is not NON_DATA_COLLECTING_NODE:
                display_data.update(self.value)

        return {self.name: display_data}
