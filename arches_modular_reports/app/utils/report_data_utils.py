from django.utils.translation import get_language

from arches.app.datatypes.datatypes import DataTypeFactory
from arches.app.models import models


def localized_text(i18n_value):
    if isinstance(i18n_value, dict):
        active_language_text = i18n_value.get(get_language())
        if active_language_text:
            return active_language_text
        populated_texts = [text for text in i18n_value.values() if text]
        if populated_texts:
            return populated_texts[0]
        return ""
    if i18n_value is None:
        return ""
    return str(i18n_value)


def file_metadata_text(file_value, field):
    metadata = file_value.get(field)
    if isinstance(metadata, dict):
        return localized_text(
            {
                language: entry.get("value", "")
                for language, entry in metadata.items()
                if isinstance(entry, dict)
            }
        )
    return metadata or ""


class EditValueDescriber:
    def __init__(self):
        self.datatype_factory = DataTypeFactory()
        self.excluded_datatypes = {
            "semantic",
            *models.DDataType.objects.filter(isgeometric=True).values_list(
                "datatype", flat=True
            ),
        }
        self.nodes_by_nodegroup_id = {}
        self.card_names_by_nodegroup_id = {}

    def card_name(self, nodegroup_id):
        if nodegroup_id not in self.card_names_by_nodegroup_id:
            card_name = (
                models.CardModel.objects.filter(nodegroup_id=nodegroup_id)
                .values_list("name", flat=True)
                .first()
            )
            self.card_names_by_nodegroup_id[nodegroup_id] = localized_text(card_name)
        return self.card_names_by_nodegroup_id[nodegroup_id]

    def nodes(self, nodegroup_id):
        if nodegroup_id not in self.nodes_by_nodegroup_id:
            nodegroup_nodes = list(
                models.Node.objects.filter(nodegroup_id=nodegroup_id)
                .exclude(datatype__in=self.excluded_datatypes)
                .prefetch_related("cardxnodexwidget_set")
                .order_by("cardxnodexwidget__sortorder")
            )
            for node in nodegroup_nodes:
                widgets = node.cardxnodexwidget_set.all()
                widget_label = localized_text(widgets[0].label) if widgets else ""
                node.report_label = widget_label or node.name
            self.nodes_by_nodegroup_id[nodegroup_id] = nodegroup_nodes
        return self.nodes_by_nodegroup_id[nodegroup_id]

    def display_value(self, tile_data, nodegroup_id, node):
        raw_value = tile_data.get(str(node.pk))
        if raw_value in (None, "", [], {}):
            return ""
        tile = models.TileModel(nodegroup_id=nodegroup_id, data=tile_data)
        datatype = self.datatype_factory.get_instance(node.datatype)
        try:
            return datatype.get_display_value(tile, node)
        except (AttributeError, KeyError, TypeError, ValueError):
            return str(raw_value)

    def describe(self, edit):
        old_tile_data = edit.oldvalue if isinstance(edit.oldvalue, dict) else None
        new_tile_data = edit.newvalue if isinstance(edit.newvalue, dict) else None
        described_values = []
        for node in self.nodes(edit.nodegroupid):
            before = None
            after = None
            if old_tile_data is not None:
                before = self.display_value(old_tile_data, edit.nodegroupid, node)
            if new_tile_data is not None:
                after = self.display_value(new_tile_data, edit.nodegroupid, node)
            old_raw_value = (old_tile_data or {}).get(str(node.pk))
            new_raw_value = (new_tile_data or {}).get(str(node.pk))
            described_values.append(
                {
                    "node_alias": node.alias,
                    "label": node.report_label,
                    "before": before,
                    "after": after,
                    "changed": old_raw_value != new_raw_value,
                }
            )
        return described_values
