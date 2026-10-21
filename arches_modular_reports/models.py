from pathlib import Path

from django.core.exceptions import ValidationError
from django.db import models

from arches import __version__ as _arches_version_str
from arches.app.models.models import GraphModel, Node, NodeGroup
from arches.app.models.system_settings import settings
from arches_modular_reports.app.utils.resource_report_config import (
    generate_resource_report_config,
    validate_resource_report_config,
)
from arches_modular_reports.utils import PrettyJSONEncoder
from packaging.version import Version

arches_version = Version(_arches_version_str)


def get_graph_choices():
    choices = models.Q(isresource=True)
    choices &= ~models.Q(pk=settings.SYSTEM_SETTINGS_RESOURCE_MODEL_ID)
    if arches_version >= Version("8.0"):
        choices &= models.Q(source_identifier=None)
    return choices


class ReportConfig(models.Model):
    id = models.AutoField(primary_key=True)
    config = models.JSONField(
        blank=True, null=False, default=dict, encoder=PrettyJSONEncoder
    )
    slug = models.TextField(default="default", blank=False, null=False)
    graph = models.ForeignKey(
        GraphModel,
        blank=False,
        on_delete=models.CASCADE,
        related_name="report_configs",
        limit_choices_to=get_graph_choices,
    )

    excluded_datatypes = {"semantic", "annotation", "geojson-feature-collection"}

    class Meta:
        managed = True
        db_table = "arches_modular_report_config"
        constraints = [
            models.UniqueConstraint(
                fields=["graph", "slug"],
                name="unique_slug_graph",
            )
        ]

    def __str__(self):
        if self.config and self.graph:
            return f"Config for: {self.graph.name}: {self.config.get('name')}"
        return super().__str__()

    def clean(self):
        if not self.graph.slug:
            raise ValidationError("Graph must have a slug")
        if not self.config:
            self.config = self.generate_config()
        self.validate_config()

    def generate_config(self):
        return generate_resource_report_config(self.graph)

    def generate_card_sections(self):
        ordered_allowed_nodes = (
            Node.objects.filter(graph=self.graph)
            .exclude(datatype__in=self.excluded_datatypes)
            .exclude(cardxnodexwidget__visible=False)
            .order_by("cardxnodexwidget__sortorder")
        )
        ordered_top_cards = (
            self.graph.cardmodel_set.filter(nodegroup__parentnodegroup__isnull=True)
            .select_related(
                "nodegroup__grouping_node"
                if arches_version >= Version("8.0")
                else "nodegroup"
            )
            .prefetch_related(
                models.Prefetch(
                    "nodegroup__node_set",
                    ordered_allowed_nodes,
                    to_attr="allowed_nodes",
                )
            )
            .order_by("sortorder")
        )

        def get_grouping_node(nodegroup):
            if arches_version >= Version("8.0"):
                return nodegroup.grouping_node
            return nodegroup.node_set.filter(pk=nodegroup.pk).first()

        return [
            {
                "name": str(card.name),
                "components": [
                    {
                        "component": "arches_modular_reports/ModularReport/components/DataSection",
                        "config": {
                            "nodegroup_alias": get_grouping_node(card.nodegroup).alias,
                            "node_aliases": [
                                node.alias for node in card.nodegroup.allowed_nodes
                            ],
                            # custom_labels: {node alias: "my custom widget label"}
                            "custom_labels": {},
                            # custom_card_name: "My Custom Card Name"
                            "custom_card_name": None,
                        },
                    }
                ],
            }
            for card in ordered_top_cards
        ]

    def validate_config(self):
        def validate_dict(config_dict):
            for key, val in config_dict.items():
                if key == "name":
                    if not isinstance(val, str):
                        raise ValidationError(f"Name is not a string: {val}")
                elif key == "components":
                    if not isinstance(val, list):
                        raise ValidationError(f"Components is not a list: {val}")
                    validate_components(val)
                elif key == "theme":
                    if not isinstance(val, str):
                        raise ValidationError(f"Theme is not a string: {val}")
                else:
                    raise ValidationError(f"Invalid key in config: {key}")

        def validate_components(components):
            for item in components:
                for key, val in item.items():
                    if key == "component":
                        if not isinstance(val, str):
                            raise ValidationError(f"Component is not a string: {val}")
                    elif key == "config":
                        if not isinstance(val, dict):
                            raise ValidationError(f"Config is not a dict: {val}")
                        validate_components_config(val)
                    else:
                        raise ValidationError(f"Invalid key in components: {key}")
                component = self.get_or_raise(item, "component", "")
                config = self.get_or_raise(item, "config", "")
                component_name = Path(component).stem.lower()
                method = getattr(self, "validate_" + component_name, lambda _: None)
                # example method: validate_datasection
                method(config)

        def validate_components_config(config_dict):
            for val in config_dict.values():
                if isinstance(val, list):
                    for list_item in val:
                        if (
                            isinstance(list_item, dict)
                            and "name" in list_item
                            and "components" in list_item
                        ):
                            validate_dict(list_item)

        validate_dict(self.config)

    def validate_resourcereport(self, resource_report_config):
        validate_resource_report_config(resource_report_config, self.graph)

    def validate_datasection(self, card_config):
        nodegroup_alias = self.get_or_raise(card_config, "nodegroup_alias", "Data")
        nodegroup = NodeGroup.objects.filter(
            node__alias=nodegroup_alias, node__graph=self.graph
        ).first()
        if not nodegroup:
            raise ValidationError(
                f"Section contains invalid nodegroup: {nodegroup_alias}"
            )

        self.validate_node_aliases(
            card_config,
            "Data",
            nodegroup.node_set.exclude(datatype__in=self.excluded_datatypes),
        )

    def validate_node_aliases(self, config, section_name, usable_nodes_queryset):
        requested_node_aliases = self.get_or_raise(config, "node_aliases", section_name)
        usable_aliases = {node.alias for node in usable_nodes_queryset}
        if extra_node_aliases := set(requested_node_aliases) - usable_aliases:
            raise ValidationError(
                f"{section_name} section contains extraneous "
                "or invalid node aliases or unsupported datatypes: "
                f"{extra_node_aliases}"
            )
        overridden_labels = set(config.get("custom_labels", {}))
        if extra_overridden_labels := overridden_labels - usable_aliases:
            raise ValidationError(
                f"{section_name} section overrides labels for "
                "extraneous or invalid node aliases or unsupported "
                f"datatypes: {extra_overridden_labels}"
            )

    @staticmethod
    def get_or_raise(config, key, section_name):
        if key not in config:
            raise ValidationError(f"{section_name} section missing key: {key}")
        return config[key]
