import re

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.functional import cached_property

from arches.app.models.models import GraphModel, NodeGroup
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

    @cached_property
    def usable_node_aliases(self):
        if not self.graph:
            return {}
        qs = self.graph.node_set.exclude(datatype__in=self.excluded_datatypes)
        return {node.alias for node in qs}

    def clean(self):
        if self.graph_id and not self.config:
            self.config = self.generate_config()
        self.validate_config()

    def generate_config(self):
        return {
            "name": "Untitled Report",
            "components": [
                {
                    "component": "ReportHeader",
                    "config": {
                        "descriptor": f"{self.graph.name} Descriptor",
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
                        "nodes": [],
                        "image": None,
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
        ordered_top_cards = (
            self.graph.cardmodel_set.filter(nodegroup__parentnodegroup__isnull=True)
            .select_related("nodegroup")
            .prefetch_related("nodegroup__node_set")
            .order_by("sortorder")
        )
        return [
            {
                "name": str(card.name),
                "components": [
                    {
                        "component": "DataSection",
                        "config": {
                            "nodegroup_id": str(card.nodegroup_id),
                            "nodes": [
                                node.alias
                                for node in sorted(
                                    card.nodegroup.node_set.all(),
                                    key=lambda node: node.sortorder or 0,
                                )
                                if node.datatype not in self.excluded_datatypes
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
            pk=settings.SYSTEM_SETTINGS_RESOURCE_MODEL_ID
        ).filter(isresource=True)
        return [
            {
                "name": str(other_graph.name),
                "components": [
                    {
                        "component": "RelatedResourcesSection",
                        "config": {
                            "graph_id": str(other_graph.pk),
                            "nodes": [],
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
        descriptor_template = header_config["descriptor"]
        substrings = self.extract_substrings(descriptor_template)
        self.validate_node_aliases({"nodes": substrings}, "Header")

    def validate_reporttombstone(self, tombstone_config):
        self.validate_node_aliases(tombstone_config, "Tombstone")

    def validate_datasection(self, card_config):
        nodegroup_id = card_config["nodegroup_id"]
        nodegroup = (
            NodeGroup.objects.filter(pk=nodegroup_id, node__graph=self.graph)
            .prefetch_related("node_set")
            .first()
        )
        if not nodegroup:
            raise ValidationError(f"Section contains invalid nodegroup: {nodegroup_id}")

        self.validate_node_aliases(card_config, "Data")

    def validate_relatedresourcessection(self, rr_config):
        if "graph_id" not in rr_config:
            raise ValidationError("Related Resources section missing graph_id")
        if "nodes" not in rr_config:
            raise ValidationError("Related Resources section missing nodes")
        try:
            graph = GraphModel.objects.get(pk=rr_config["graph_id"])
        except GraphModel.DoesNotExist:
            raise ValidationError("Related Resources section contains invalid graph id")

        related_graph_usable_aliases = graph.node_set.exclude(
            datatype__in=self.excluded_datatypes
        )
        usable_aliases = {node.alias for node in related_graph_usable_aliases}
        self.validate_node_aliases(rr_config, "Related Resources", usable_aliases)

    def validate_node_aliases(self, config, section_name, usable_aliases=None):
        if usable_aliases is None:
            usable_aliases = self.usable_node_aliases
        requested_node_aliases = set(config.get("nodes", {}))
        if extra_node_aliases := requested_node_aliases - usable_aliases:
            raise ValidationError(
                f"{section_name} section contains extraneous "
                f"aliases or unsupported datatypes: {extra_node_aliases}"
            )
        overridden_labels = set(config.get("custom_labels", {}))
        if extra_overridden_labels := overridden_labels - usable_aliases:
            raise ValidationError(
                f"{section_name} section contains extraneous "
                f"overridden labels for nodes: {extra_overridden_labels}"
            )

    @staticmethod
    def extract_substrings(template_string):
        pattern = r"<(.*?)>"
        substrings = re.findall(pattern, template_string)

        return substrings
