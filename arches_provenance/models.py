import re

from django.core.exceptions import ValidationError
from django.db import models

from arches.app.models.models import GraphModel, NodeGroup


class ReportConfig(models.Model):
    id = models.AutoField(primary_key=True)
    config = models.JSONField(blank=True, null=False, default=dict)
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
            "name": "Untitled Report",  # Not user-facing: shows in django admin.
            "descriptor_template": f"{self.graph.name} Descriptor",
            "tools": {
                "export_formats": ["csv", "json-ld", "rdf"],
            },
            "tabs": ["Data", "Related Resources"],
            "tombstone_nodes": [],
            "image": None,  # TBD
            "sections": self.generate_sections(),
        }

    def generate_sections(self):
        ordered_cards = (
            self.graph.cardmodel_set.filter(nodegroup__parentnodegroup__isnull=True)
            .select_related("nodegroup")
            .prefetch_related("nodegroup__node_set")
            .order_by("sortorder")
        )
        return [
            {
                "label": str(card.name),
                "nodegroup_id": str(card.nodegroup_id),
                "nodes": [
                    node.alias
                    for node in sorted(
                        card.nodegroup.node_set.all(),
                        key=lambda node: int(node.sortorder or 0),
                    )
                    if node.datatype != "semantic"
                ],
                # Name of a Vue component.
                "content": "LinkedSection",
            }
            for card in ordered_cards
        ]

    def validate_config(self):
        expected_keys = set(
            [
                "name",
                "descriptor_template",
                "tools",
                "tabs",
                "tombstone_nodes",
                "image",
                "sections",
            ]
        )
        actual_keys = set(self.config)
        if expected_keys != actual_keys:
            raise ValidationError(
                f"Expected keys: {expected_keys}. Actual keys: {actual_keys}"
            )
        self.validate_descriptor_template(self.config["descriptor_template"])
        self.validate_tombstone_nodes(self.config["tombstone_nodes"])
        for section in self.config["sections"]:
            self.validate_section(section)

    def validate_descriptor_template(self, descriptor_template):
        substrings = self.extract_substrings(descriptor_template)
        nodes = self.graph.node_set.filter(alias__in=substrings)
        if len(nodes) != len(substrings):
            raise ValidationError("Descriptor template contains invalid node aliases.")

    def validate_tombstone_nodes(self, tombstone_nodes):
        nodes = self.graph.node_set.filter(alias__in=tombstone_nodes)
        if len(nodes) != len(tombstone_nodes):
            raise ValidationError("Tombstone config contains invalid node aliases.")

    def validate_section(self, section):
        if not section.get("label"):
            raise ValidationError("A label is required for each section.")
        if not section.get("content"):
            raise ValidationError("A Vue component is required for each section.")
        nodegroup = (
            NodeGroup.objects.filter(pk=section["nodegroup_id"], node__graph=self.graph)
            .prefetch_related("node_set")
            .first()
        )
        if not nodegroup:
            raise ValidationError("Sections contain invalid nodegroup ids.")
        aliases = [node.alias for node in nodegroup.node_set.all()]
        for alias in section["nodes"]:
            if alias not in aliases:
                raise ValidationError(f"Section contains invalid node alias: {alias}")

    @staticmethod
    def extract_substrings(template_string):
        pattern = r"<(.*?)>"
        substrings = re.findall(pattern, template_string)

        return substrings
