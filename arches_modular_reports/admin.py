from django.contrib import admin
from django.db import models
from django.forms import Textarea

from arches_modular_reports.models import ReportConfig


class ReportConfigAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.JSONField: {"widget": Textarea(attrs={"rows": 32, "cols": 100})},
    }


admin.site.register(ReportConfig, ReportConfigAdmin)
