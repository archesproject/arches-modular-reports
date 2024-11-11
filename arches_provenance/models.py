from django.db import models

from arches.app.models.models import GraphModel


class ReportConfig(models.Model):
    id = models.AutoField(primary_key=True)
    config = models.JSONField(blank=True, null=False, default=dict)
    graph = models.OneToOneField(
        GraphModel, blank=False, on_delete=models.CASCADE, related_name="report"
    )

    class Meta:
        managed = True
        db_table = "arches_provenance_report_config"

    def __str__(self):
        return f"Config for: {self.graph.name}"

    def clean(self):
        if self.graph_id and not self.config:
            self.config = self.generate_config()

    def generate_config(self):
        return {
            "descriptor": {},
            "tools": {
                "lists": True,
                "export_formats": ["csv", "json-ld", "rdf"],
            },
            "tombstone_nodes": [],
            "sections": [
                {
                    "name": str(card.name),
                    "nodegroup_id": str(card.nodegroup_id),
                    "nodes": [
                        node.alias
                        for node in sorted(
                            card.nodegroup.node_set.all(),
                            key=lambda node: int(node.sortorder or 0),
                        )
                        if node.datatype != "semantic"
                    ],
                }
                for card in self.graph.cardmodel_set.filter(
                    nodegroup__parentnodegroup__isnull=True
                )
                .select_related("nodegroup")
                .prefetch_related("nodegroup__node_set")
                .order_by("sortorder")
            ],
        }
