import re
from pathlib import Path

from django.core.exceptions import ValidationError
from django.db import models

from arches import VERSION as arches_version
from arches.app.models.models import GraphModel, Node, NodeGroup
from arches.app.models.system_settings import settings
from arches_modular_reports.utils import PrettyJSONEncoder


def get_graph_choices():
    choices = models.Q(isresource=True)
    choices &= ~models.Q(pk=settings.SYSTEM_SETTINGS_RESOURCE_MODEL_ID)
    if arches_version >= (8, 0):
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

    @property
    def excluded_datatypes(self):
        return {"semantic", "annotation", "geojson-feature-collection"}

    def clean(self):
        if not self.graph.slug:
            raise ValidationError("Graph must have a slug")
        if not self.config:
            self.config = self.generate_config()
        self.validate_config()

    def generate_config(self):
        return {
            "name": "Untitled Report",
            "components": [
                {
                    "component": "arches_modular_reports/ModularReport/components/ReportHeader",
                    "config": {
                        "descriptor": f"{self.graph.name} descriptor template",
                        "node_alias_options": {},  # e.g. limit, separator
                    },
                },
                {
                    "component": "arches_modular_reports/ModularReport/components/ReportToolbar",
                    "config": {
                        "lists": True,
                        "export_formats": ["csv", "json-ld", "json"],
                    },
                },
                {
                    "component": "arches_modular_reports/ModularReport/components/ReportTombstone",
                    "config": {
                        "node_aliases": [],
                        "image_node_alias": None,
                        "custom_labels": {},
                    },
                },
                {
                    "component": "arches_modular_reports/ModularReport/components/ReportTabs",
                    "config": {
                        "tabs": [
                            {
                                "name": "Data",
                                "components": [
                                    {
                                        "component": "arches_modular_reports/ModularReport/components/LinkedSections",
                                        "config": {
                                            "sections": self.generate_card_sections()
                                        },
                                    },
                                ],
                            },
                            {
                                "name": "Related Resources",
                                "components": [
                                    {
                                        "component": "arches_modular_reports/ModularReport/components/LinkedSections",
                                        "config": {
                                            "sections": self.generate_related_resources_sections()
                                        },
                                    },
                                ],
                            },
                        ],
                    },
                },
            ],
        }

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
                "nodegroup__grouping_node" if arches_version >= (8, 0) else "nodegroup"
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
            if arches_version >= (8, 0):
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

    def generate_related_resources_sections(self):
        other_graphs = GraphModel.objects.exclude(
            pk=settings.SYSTEM_SETTINGS_RESOURCE_MODEL_ID,
        ).filter(
            slug__isnull=False,
            isresource=True,
        )
        if arches_version >= (8, 0):
            other_graphs = other_graphs.filter(source_identifier=None)
        return [
            {
                "name": str(other_graph.name),
                "components": [
                    {
                        "component": "arches_modular_reports/ModularReport/components/RelatedResourcesSection",
                        "config": {
                            "graph_slug": other_graph.slug,
                            "node_aliases": [],
                            "custom_labels": {},
                        },
                    },
                ],
            }
            for other_graph in other_graphs
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
                # example method: validate_relatedresourcessection
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

    def validate_reportheader(self, header_config):
        descriptor_template = self.get_or_raise(header_config, "descriptor", "Header")
        if not isinstance(descriptor_template, str):
            raise ValidationError("Descriptor is not a string")
        substrings = self.extract_node_aliases(descriptor_template)
        usable_nodes = self.graph.node_set.exclude(datatype__in=self.excluded_datatypes)
        self.validate_node_aliases(
            {"node_aliases": substrings},
            "Header",
            usable_nodes,
        )
        if node_alias_options := header_config.get("node_alias_options"):
            self.validate_node_aliases(
                {"node_aliases": node_alias_options.keys()},
                "Header",
                usable_nodes,
            )
            self.validate_options(node_alias_options)

    def validate_reporttombstone(self, tombstone_config):
        self.validate_node_aliases(
            tombstone_config,
            "Tombstone",
            self.graph.node_set.exclude(datatype__in=self.excluded_datatypes),
        )
        if image_node_alias := tombstone_config.get("image_node_alias"):
            if not self.graph.node_set.filter(
                alias=image_node_alias, datatype="file-list"
            ).exists():
                msg = f"Tombstone section contains invalid image node alias: {image_node_alias}"
                raise ValidationError(msg)

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

    def validate_relatedresourcessection(self, rr_config):
        slug = self.get_or_raise(rr_config, "graph_slug", "Related Resources")
        filters = models.Q(slug=slug)
        if arches_version >= (8, 0):
            filters &= models.Q(source_identifier=None)
        try:
            graph = GraphModel.objects.get(filters)
        except (GraphModel.DoesNotExist, GraphModel.MultipleObjectsReturned):
            msg = "Related Resources section contains invalid graph slug"
            raise ValidationError(msg)

        usable_related_nodes = graph.node_set.exclude(
            datatype__in=self.excluded_datatypes
        )
        self.validate_node_aliases(rr_config, "Related Resources", usable_related_nodes)

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

    def validate_options(self, options):
        for alias, option_mapping in options.items():
            for key, val in option_mapping.items():
                match key:
                    case "limit":
                        if not isinstance(val, int):
                            raise ValidationError(
                                f"Limit for {alias} is not an integer"
                            )
                    case "separator":
                        if not isinstance(val, str):
                            raise ValidationError(
                                f"Separator for {alias} is not a string"
                            )
                    case _:
                        raise ValidationError(f"Invalid option for {alias}")

    @staticmethod
    def extract_node_aliases(template_string):
        alias_pattern = r"<(.*?)>"
        options_pattern = r"\[(.*?)\]"
        result = []
        for substring in re.findall(alias_pattern, template_string):
            if option_matches := re.findall(options_pattern, substring):
                if len(option_matches) > 1:
                    raise ValidationError("Too many options")
                result.append(re.sub(options_pattern, "", substring, count=1))
            else:
                result.append(substring)
        return result

    @staticmethod
    def get_or_raise(config, key, section_name):
        if key not in config:
            raise ValidationError(f"{section_name} section missing key: {key}")
        return config[key]
