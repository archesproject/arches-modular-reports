from django.db import models

from arches.app.models.models import GraphModel


class ReportConfig(models.Model):
    id = models.AutoField(primary_key=True)
    config = models.JSONField(blank=True, null=False, default=dict)
    graph = models.ForeignKey(GraphModel, blank=False, on_delete=models.CASCADE)

    class Meta:
        managed = True
        db_table = "arches_provenance_report_config"

    def clean(self):
        if not self.config:
            self.config = self.generate_config()

    def generate_config(self):
        return {
            str(card.name): []
            for card in self.graph.cardmodel_set.order_by("sortorder")
        }
