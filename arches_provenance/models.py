import re

from django.core.exceptions import ValidationError
from django.db import models

from arches.app.models.models import GraphModel, Node, NodeGroup
from arches.app.models.system_settings import settings
from arches_provenance.utils import PrettyJSONEncoder


class ReportConfig(models.Model):
    id = models.AutoField(primary_key=True)
    config = models.JSONField(
        blank=True, null=False, default=dict, encoder=PrettyJSONEncoder
    )
    graph = models.ForeignKey(
        GraphModel, blank=False, on_delete=models.CASCADE, related_name="report"
    )

    class Meta:
        managed = True
        db_table = "arches_provenance_report_config"

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
                    "component": "ReportHeader",
                    "config": {
                        "descriptor": f"{self.graph.name} descriptor template",
                    },
                },
                {
                    "component": "ReportToolbar",
                    "config": {
                        "lists": True,
                        "export_formats": ["csv", "json-ld", "json"],
                    },
                },
                {
                    "component": "ReportTombstone",
                    "config": {
                        "node_aliases": [],
                        "image_node_alias": None,
                        "custom_labels": {},
                    },
                },
                {
                    "component": "ReportTabs",
                    "config": {
                        "tabs": [
                            {
                                "name": "Data",
                                "components": [
                                    {
                                        "component": "LinkedSections",
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
                                        "component": "LinkedSections",
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
            Node.objects.filter(cardxnodexwidget__visible=True)
            .exclude(datatype__in=self.excluded_datatypes)
            .order_by("cardxnodexwidget__sortorder")
        )
        ordered_top_cards = (
            self.graph.cardmodel_set.filter(nodegroup__parentnodegroup__isnull=True)
            .select_related("nodegroup")
            .prefetch_related(
                models.Prefetch(
                    "nodegroup__node_set",
                    ordered_allowed_nodes,
                    to_attr="allowed_nodes",
                )
            )
            .order_by("sortorder")
        )
        return [
            {
                "name": str(card.name),
                "components": [
                    {
                        "component": "DataSection",
                        "config": {
                            # TODO: arches v8: card.nodegroup.grouping_node.alias
                            "nodegroup_alias": card.nodegroup.node_set.filter(
                                pk=card.nodegroup.pk
                            )
                            .first()
                            .alias,
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
        )  # TODO: arches v8: add source_identifier=None
        return [
            {
                "name": str(other_graph.name),
                "components": [
                    {
                        "component": "RelatedResourcesSection",
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
            for k, v in config_dict.items():
                if k == "name":
                    if not isinstance(v, str):
                        raise ValidationError(f"Name is not a string: {v}")
                elif k == "components":
                    if not isinstance(v, list):
                        raise ValidationError(f"Components is not a list: {v}")
                    validate_components(v)
                else:
                    raise ValidationError(f"Invalid key in config: {k}")

        def validate_components(components):
            for item in components:
                for k, v in item.items():
                    if k == "component":
                        if not isinstance(v, str):
                            raise ValidationError(f"Component is not a string: {v}")
                    elif k == "config":
                        if not isinstance(v, dict):
                            raise ValidationError(f"Config is not a dict: {v}")
                        validate_components_config(v)
                    else:
                        raise ValidationError(f"Invalid key in components: {k}")
                method = getattr(
                    self, "validate_" + item["component"].lower(), lambda noop: None
                )
                # example method: validate_relatedresourcessection
                method(item["config"])

        def validate_components_config(config_dict):
            for v in config_dict.values():
                if isinstance(v, list):
                    for list_item in v:
                        if (
                            isinstance(list_item, dict)
                            and "name" in list_item
                            and "components" in list_item
                        ):
                            validate_dict(list_item)

        validate_dict(self.config)

    def validate_reportheader(self, header_config):
        descriptor_template = self.get_or_raise(header_config, "descriptor", "Header")
        substrings = self.extract_substrings(descriptor_template)
        self.validate_node_aliases(
            {"node_aliases": substrings},
            "Header",
            self.graph.node_set.exclude(datatype__in=self.excluded_datatypes),
        )

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
        try:
            # TODO: arches v8: add source_identifier=None
            graph = GraphModel.objects.get(slug=slug)
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

    @staticmethod
    def extract_substrings(template_string):
        pattern = r"<(.*?)>"
        substrings = re.findall(pattern, template_string)

        return substrings

    @staticmethod
    def get_or_raise(config, key, section_name):
        if key not in config:
            raise ValidationError(f"{section_name} missing key: {key}")
        return config[key]
