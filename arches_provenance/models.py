from django.db import models

from arches.app.models.models import GraphModel


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
        return f"Config for: {self.graph.name}: {self.config.get("name")}"

    def clean(self):
        if self.graph_id and not self.config:
            self.config = self.generate_config()

    def generate_config(self):
        # This will be fleshed out in a future PR.
        return {
            "name": "Untitled Report",  # Not user-facing: shows in django admin.
            "descriptor": {},
            "tools": {
                "lists": True,
                "export_formats": ["csv", "json-ld", "rdf"],
            },
            "tombstone_nodes": [],
            "sections": [],
        }
