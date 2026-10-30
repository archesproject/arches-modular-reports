from arches.app.datatypes.datatypes import DataTypeFactory
from arches.app.models import models

from arches_modular_reports.models import ReportConfig


class EditValueDescriber:
    def __init__(self, nodegroup_ids):
        self.datatype_factory = DataTypeFactory()
        self.card_names_by_nodegroup_id = {}
        for nodegroup_id, card_name in models.CardModel.objects.filter(
            nodegroup_id__in=nodegroup_ids
        ).values_list("nodegroup_id", "name"):
            self.card_names_by_nodegroup_id.setdefault(
                str(nodegroup_id), str(card_name or "")
            )
        self.nodes_by_nodegroup_id = {}
        for node in (
            models.Node.objects.filter(nodegroup_id__in=nodegroup_ids)
            .exclude(datatype__in=ReportConfig.excluded_datatypes)
            .order_by("cardxnodexwidget__sortorder")
        ):
            self.nodes_by_nodegroup_id.setdefault(str(node.nodegroup_id), []).append(
                node
            )

    def display_value(self, tile_data, nodegroup_id, node):
        raw_value = tile_data.get(str(node.pk))
        if raw_value is None:
            return ""
        tile = models.TileModel(nodegroup_id=nodegroup_id, data=tile_data)
        datatype = self.datatype_factory.get_instance(node.datatype)
        try:
            return datatype.get_display_value(tile, node)
        except (AttributeError, KeyError, TypeError, ValueError):
            return str(raw_value)

    def describe(self, edit):
        described_values = []
        for node in self.nodes_by_nodegroup_id.get(edit.nodegroupid, []):
            before = None
            after = None
            old_raw_value = None
            new_raw_value = None
            if edit.oldvalue is not None:
                before = self.display_value(edit.oldvalue, edit.nodegroupid, node)
                old_raw_value = edit.oldvalue.get(str(node.pk))
            if edit.newvalue is not None:
                after = self.display_value(edit.newvalue, edit.nodegroupid, node)
                new_raw_value = edit.newvalue.get(str(node.pk))
            described_values.append(
                {
                    "node_alias": node.alias,
                    "before": before,
                    "after": after,
                    "changed": old_raw_value != new_raw_value,
                }
            )
        return described_values
