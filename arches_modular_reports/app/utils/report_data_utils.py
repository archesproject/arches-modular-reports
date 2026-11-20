from collections import Counter

from django.db.models.fields.json import KT
from django.db.models.functions import Coalesce
from django.utils.translation import get_language, ngettext

from arches.app.datatypes.datatypes import DataTypeFactory
from arches.app.models import models
from arches.app.models.system_settings import settings

from arches_modular_reports.models import ReportConfig

GEOMETRY_KINDS_BY_TYPE = {
    "Point": "point",
    "MultiPoint": "point",
    "LineString": "line",
    "MultiLineString": "line",
    "Polygon": "polygon",
    "MultiPolygon": "polygon",
}


def language_names_by_code():
    return dict(models.Language.objects.values_list("code", "name"))


def localized_text_field(field_name):
    return Coalesce(
        KT(f"{field_name}__{get_language()}"),
        KT(f"{field_name}__{settings.LANGUAGE_CODE}"),
    )


def in_display_language(values_by_language):
    for language_code in (get_language(), settings.LANGUAGE_CODE):
        if value := values_by_language.get(language_code):
            return value
    return next((value for value in values_by_language.values() if value), None)


def localized_file_text(file_value, key):
    return in_display_language(
        {
            language_code: text.get("value")
            for language_code, text in (file_value.get(key) or {}).items()
        }
    )


def is_localized_text(raw_value):
    return (
        isinstance(raw_value, dict)
        and len(raw_value) > 0
        and all(
            isinstance(language_value, dict)
            and isinstance(language_value.get("value"), str)
            for language_value in raw_value.values()
        )
    )


def describe_localized_text(raw_value, language_names):
    active_language = get_language()
    texts = [
        (language_code, language_value["value"])
        for language_code, language_value in raw_value.items()
        if language_value["value"].strip()
    ]
    texts.sort(key=lambda text: text[0] != active_language)
    descriptions = []
    for language_code, text in texts:
        if language_code == active_language:
            descriptions.append(text)
        else:
            language_name = language_names.get(language_code, language_code)
            descriptions.append(f"{text} ({language_name})")
    return "; ".join(descriptions)


def describe_geometry_kind(kind, count):
    if kind == "point":
        return ngettext("%(count)d point", "%(count)d points", count) % {"count": count}
    if kind == "line":
        return ngettext("%(count)d line", "%(count)d lines", count) % {"count": count}
    if kind == "polygon":
        return ngettext("%(count)d polygon", "%(count)d polygons", count) % {
            "count": count
        }
    return ngettext("%(count)d shape", "%(count)d shapes", count) % {"count": count}


def describe_feature_collection(feature_collection):
    if not isinstance(feature_collection, dict):
        return ""
    kind_counts = Counter(
        GEOMETRY_KINDS_BY_TYPE.get((feature.get("geometry") or {}).get("type"), "")
        for feature in feature_collection.get("features") or []
        if isinstance(feature, dict)
    )
    return ", ".join(
        describe_geometry_kind(kind, count) for kind, count in kind_counts.items()
    )


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
        self.language_names = language_names_by_code()
        self.geometric_datatypes = set(
            models.DDataType.objects.filter(isgeometric=True).values_list(
                "datatype", flat=True
            )
        )
        self.nodes_by_nodegroup_id = {}
        for node in (
            models.Node.objects.filter(nodegroup_id__in=nodegroup_ids)
            .exclude(
                datatype__in=ReportConfig.excluded_datatypes - self.geometric_datatypes
            )
            .order_by("cardxnodexwidget__sortorder")
        ):
            self.nodes_by_nodegroup_id.setdefault(str(node.nodegroup_id), []).append(
                node
            )

    def display_value(self, tile_data, nodegroup_id, node):
        raw_value = tile_data.get(str(node.pk))
        if raw_value is None:
            return ""
        if node.datatype in self.geometric_datatypes:
            return describe_feature_collection(raw_value)
        if is_localized_text(raw_value):
            return describe_localized_text(raw_value, self.language_names)
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
