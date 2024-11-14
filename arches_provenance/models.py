import re

from django.core.exceptions import ValidationError
from django.db import models

from arches.app.models.models import GraphModel, NodeGroup
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
        return f"Config for: {self.graph.name}: {self.config.get('name')}"

    def clean(self):
        if self.graph_id and not self.config:
            self.config = self.generate_config()
        self.validate_config()

    def generate_config(self):
        return {
            "name": "Untitled Report",
            "content": [
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
                        "export_formats": ["CSV", "JSON-LD", "RDF"],
                    },
                },
                {
                    "component": "ReportTombstone",
                    "config": {
                        "nodes": [],
                        "image": None,
                    },
                },
                {
                    "component": "ReportTabs",
                    "config": {
                        "tabs": [
                            {
                                "name": "Data",
                                "content": [
                                    {
                                        "component": "CardSections",
                                        "config": {
                                            "sections": self.generate_card_sections()
                                        },
                                    },
                                ],
                            },
                            {
                                "name": "Related Resources",
                                "content": [
                                    {
                                        "component": "RelatedResourcesSections",
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
                "content": [
                    {
                        "component": "CardSection",
                        "config": {
                            "nodegroup_id": str(card.nodegroup_id),
                            "nodes": [
                                node.alias
                                for node in sorted(
                                    card.nodegroup.node_set.all(),
                                    key=lambda node: int(node.sortorder or 0),
                                )
                                if node.datatype != "semantic"
                            ],
                        },
                    }
                ],
            }
            for card in ordered_top_cards
        ]

    def generate_related_resources_sections(self):
        top_node = self.graph.node_set.get(istopnode=True)
        relatable_graphs = GraphModel.objects.filter(
            pk__in=top_node.get_relatable_resources()
        )
        return [
            {
                "name": str(relatable_graph.name),  # not pluralized
                "content": [
                    {
                        "component": "RelatedResourcesSection",
                        "config": {
                            "graph_id": str(relatable_graph.graph_id),
                            "nodes": [],  # could generate this once we have more test data
                        },
                    }
                ],
            }
            for relatable_graph in relatable_graphs
        ]

    def validate_config(self):
        def validate_dict(config_dict):
            for k, v in config_dict.items():
                if k == "name":
                    if not isinstance(v, str):
                        raise ValidationError(f"Name is not a string: {v}")
                elif k == "content":
                    if not isinstance(v, list):
                        raise ValidationError(f"Content is not a list: {v}")
                    validate_content(v)
                else:
                    raise ValidationError(f"Invalid key in config: {k}")

        def validate_content(content):
            for item in content:
                for k, v in item.items():
                    if k == "component":
                        if not isinstance(v, str):
                            raise ValidationError(f"Component is not a string: {v}")
                    elif k == "config":
                        if not isinstance(v, dict):
                            raise ValidationError(f"Config is not a dict: {v}")
                        validate_content_config(v)
                    else:
                        raise ValidationError(f"Invalid key in content: {k}")
                getattr(
                    self, "validate_" + item["component"].lower(), lambda noop: None
                )(item["config"])

        def validate_content_config(config_dict):
            for v in config_dict.values():
                if isinstance(v, list):
                    for list_item in v:
                        if (
                            isinstance(list_item, dict)
                            and "name" in list_item
                            and "content" in list_item
                        ):
                            validate_dict(list_item)

        validate_dict(self.config)

    def validate_reportheader(self, header_config):
        descriptor_template = header_config["descriptor"]
        substrings = self.extract_substrings(descriptor_template)
        nodes = self.graph.node_set.filter(alias__in=substrings)
        if len(nodes) != len(substrings):
            raise ValidationError("Descriptor template contains invalid node aliases.")

    def validate_reporttombstone(self, tombstone_config):
        tombstone_nodes = tombstone_config["nodes"]
        nodes = self.graph.node_set.filter(alias__in=tombstone_nodes)
        if len(nodes) != len(tombstone_nodes):
            raise ValidationError("Tombstone config contains invalid node aliases.")

    def validate_cardsection(self, card_config):
        nodegroup_id = card_config["nodegroup_id"]
        nodegroup = (
            NodeGroup.objects.filter(pk=nodegroup_id, node__graph=self.graph)
            .prefetch_related("node_set")
            .first()
        )
        if not nodegroup:
            raise ValidationError(f"Section contains invalid nodegroup: {nodegroup_id}")
        aliases = [node.alias for node in nodegroup.node_set.all()]
        for alias in card_config["nodes"]:
            if alias not in aliases:
                raise ValidationError(f"Section contains invalid node alias: {alias}")

    @staticmethod
    def extract_substrings(template_string):
        pattern = r"<(.*?)>"
        substrings = re.findall(pattern, template_string)

        return substrings
