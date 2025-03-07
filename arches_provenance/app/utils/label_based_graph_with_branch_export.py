from functools import partial

from django.utils.translation import get_language

from arches.app.models.models import Value
from arches.app.utils.label_based_graph_v2 import LabelBasedGraph, LabelBasedNode


def concept_get_value(self, valueid):
    try:
        saved_value = Value.objects.prefetch_related("concept__value_set").get(
            pk=valueid
        )
    except Value.DoesNotExist:
        return Value()
    user_language = get_language()
    for other_value in saved_value.concept.value_set.all():
        if (
            other_value.language_id == user_language
            and other_value.valuetype_id == saved_value.valuetype_id
        ):
            return other_value
    return saved_value


class LabelBasedGraphWithBranchExport(LabelBasedGraph):
    """
    Override to:
    1. avoid parent_tree still being None after checking parent_tile.
    2. Use the request language for concept display values.
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

        return parent_tree

    @classmethod
    def _get_display_value(cls, tile, serialized_node, datatype_factory):
        # Swap in a better to_json() method for some datatypes.
        dt_instance = datatype_factory.get_instance(serialized_node["datatype"])
        class_name = dt_instance.__class__.__name__
        if serialized_node["datatype"] in {"concept", "concept-list"}:
            datatype_factory._datatype_instances[class_name].get_value = partial(
                concept_get_value, dt_instance
            )

        return super()._get_display_value(tile, serialized_node, datatype_factory)
