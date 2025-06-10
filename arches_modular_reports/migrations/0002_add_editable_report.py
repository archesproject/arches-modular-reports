import uuid

from django.db import migrations

template_pk = uuid.UUID("b0908227-ecc2-48dd-931b-314a9031caa0")


class Migration(migrations.Migration):

    dependencies = [
        ("arches_modular_reports", "0001_initial"),
    ]

    def create_template(apps, schema_editor):
        ReportTemplate = apps.get_model("models", "ReportTemplate")
        ReportTemplate(
            pk=template_pk,
            name="Modular Report Template",
            description="A modular report template.",
            component="reports/modular-report",
            componentname="modular-report",
            defaultconfig={},
            preload_resource_data=False,
        ).save()

    def delete_template(apps, schema_editor):
        ReportTemplate = apps.get_model("models", "ReportTemplate")
        ReportTemplate.objects.filter(pk=template_pk).delete()

    operations = [
        migrations.RunPython(create_template, delete_template),
    ]
