from django.contrib import admin

from arches_provenance import models

admin.site.register([models.ReportConfig])
# TODO: pretty-print the config field.
# https://stackoverflow.com/questions/64555011/pretty-print-django-db-models-jsonfield-in-django-admin
