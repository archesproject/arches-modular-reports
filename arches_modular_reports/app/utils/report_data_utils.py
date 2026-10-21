from arches.app.datatypes.datatypes import DataTypeFactory
from arches.app.models import models

from arches_modular_reports.models import ReportConfig


class EditValueDescriber:
    def __init__(self):
        self.datatype_factory = DataTypeFactory()
        self.nodes_by_nodegroup_id = {}
        self.card_names_by_nodegroup_id = {}

    def card_name(self, nodegroup_id):
        if nodegroup_id not in self.card_names_by_nodegroup_id:
            card_name = (
                models.CardModel.objects.filter(nodegroup_id=nodegroup_id)
                .values_list("name", flat=True)
                .first()
            )
            self.card_names_by_nodegroup_id[nodegroup_id] = str(card_name or "")
        return self.card_names_by_nodegroup_id[nodegroup_id]

    def nodes(self, nodegroup_id):
        if nodegroup_id not in self.nodes_by_nodegroup_id:
            self.nodes_by_nodegroup_id[nodegroup_id] = list(
                models.Node.objects.filter(nodegroup_id=nodegroup_id)
                .exclude(datatype__in=ReportConfig.excluded_datatypes)
                .order_by("cardxnodexwidget__sortorder")
            )
        return self.nodes_by_nodegroup_id[nodegroup_id]

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
        for node in self.nodes(edit.nodegroupid):
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
