from django.db import models

from arches.app.models.models import GraphModel


class ReportConfig(models.Model):
    id = models.AutoField(primary_key=True)
    config = models.JSONField()
    graph = models.ForeignKey(GraphModel, on_delete=models.CASCADE) 

    class Meta:
        managed = True
        db_table = "report_config"
