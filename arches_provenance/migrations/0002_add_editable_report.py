# -*- coding: utf-8 -*-

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("arches_provenance", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            """
            INSERT INTO report_templates (
                templateid,
                name,
                description,
                component,
                componentname,
                defaultconfig,
                preload_resource_data
            ) VALUES (
                'b0908227-ecc2-48dd-931b-314a9031caa0',
                'Editable Report Template',
                'An editable report for Provenance Groups.',
                'reports/editable-report',
                'editable-report',
                '{}',
                False
            );
            """,
            """
            DELETE FROM report_templates 
            WHERE templateid = 'b0908227-ecc2-48dd-931b-314a9031caa0';
            """,
        )
    ]
