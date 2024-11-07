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
            str(card.name): []
            for card in self.graph.cardmodel_set.order_by("sortorder")
        }
