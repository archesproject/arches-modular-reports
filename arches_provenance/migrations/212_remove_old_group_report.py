from django.db import migrations
from arches.app.models.models import ReportTemplate


class Migration(migrations.Migration):
    dependencies = [
        ("arches_provenance", "0006_exclude_branches_from_choices"),
    ]

    def forwards_func(apps, schema_editor):
        ReportTemplate.objects.filter(componentname="provenance_group_report").delete()

    def reverse_func(apps, schema_editor):
        pass

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
