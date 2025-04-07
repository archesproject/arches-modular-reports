import uuid
import glob
import os
import json

from django.db import migrations

from arches.app.models.system_settings import settings


class Migration(migrations.Migration):

    dependencies = [
        ("arches_provenance", "15550_delete_map"),
    ]

    def update_report_configs(apps, schema_editor):
        ReportConfig = apps.get_model("arches_provenance", "ReportConfig")
        Graph = apps.get_model("models", "GraphModel")
        ReportTemplate = apps.get_model("models", "ReportTemplate")
        editable_report_template = ReportTemplate.objects.get(
            name="Editable Report Template"
        )

        reports_dir = os.path.join(settings.APP_ROOT, "report_configs", "*.json")
        config_files = glob.glob(reports_dir)
        for config_file in config_files:
            with open(config_file) as f:
                data = json.load(f)
                try:
                    graph = Graph.objects.get(
                        slug=config_file.split("/")[-1].split(".")[0]
                    )
                    graph.template = editable_report_template
                    graph.save()
                    ReportConfig.objects.update_or_create(
                        graph=graph, defaults={"config": data}
                    )
                    # print(f"Loading: {graph.name}")
                except Graph.DoesNotExist:
                    print(
                        f"\n     Graph with slug \"{config_file.split('/')[-1].split('.')[0]}\" not found based on the report config file with the same name."
                    )

    def revert_report_configs(apps, schema_editor):
        ReportConfig = apps.get_model("arches_provenance", "ReportConfig")
        Graph = apps.get_model("models", "GraphModel")
        ReportTemplate = apps.get_model("models", "ReportTemplate")
        basic_report_template = ReportTemplate.objects.get(name="No Header Template")

        reports_dir = os.path.join(settings.APP_ROOT, "report_configs", "*.json")
        config_files = glob.glob(reports_dir)
        for config_file in config_files:
            try:
                graph = Graph.objects.get(slug=config_file.split("/")[-1].split(".")[0])
                graph.template = basic_report_template
                graph.save()
                ReportConfig.objects.filter(graph=graph).delete()
                # print(f"Reverting {graph.name} graph to Default Report Template")
            except Exception as e:
                pass

    operations = [
        migrations.RunPython(update_report_configs, revert_report_configs),
    ]
