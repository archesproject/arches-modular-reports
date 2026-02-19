import os
import json
import glob
from arches.app.models.system_settings import settings
from arches.app.models import models
from arches_modular_reports.models import ReportConfig
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _
from pathlib import Path


class Command(BaseCommand):
    """
    Commands for managing report configurations

    """

    def add_arguments(self, parser):
        parser.add_argument("operation", type=str, help='Either "load" or "write"')

        parser.add_argument(
            "-s",
            "--source",
            action="store",
            dest="source",
            help="Source location of report configs",
        )

        parser.add_argument(
            "-d",
            "--dest",
            action="store",
            dest="dest",
            help="Destination location of report configs",
        )

        parser.add_argument(
            "-o",
            "--operation",
            action="store",
            dest="operation",
            help="Operation",
        )

    def handle(self, *args, **options):
        if options["operation"] == "load":
            if options["source"]:
                self.load_report_configs(options["source"])
            elif os.path.exists(os.path.join(settings.APP_ROOT, "report_configs")):
                source = os.path.join(settings.APP_ROOT, "report_configs/**")
                self.load_report_configs(source)

        elif options["operation"] == "write":
            if options["dest"]:
                self.write_report_configs(options["dest"])
            elif os.path.exists(os.path.join(settings.APP_ROOT, "report_configs")):
                dest = os.path.join(settings.APP_ROOT, "report_configs")
                self.write_report_configs(dest=dest)

    def write_report_configs(self, dest, slug=None):
        if slug:
            configs = ReportConfig.objects.filter(slug=slug)
        else:
            configs = ReportConfig.objects.all()
        for config in configs:
            if not os.path.exists(os.path.join(dest, config.graph.slug)):
                os.makedirs(os.path.join(dest, config.graph.slug))
            file_path = os.path.join(dest, config.graph.slug, f"{config.slug}.json")
            with open(file_path, "w") as f:
                json.dump(config.config, f, indent=2)

    def load_report_configs(self, reports_dir):
        editable_report_template = models.ReportTemplate.objects.get(
            name="Modular Report Template"
        )
        config_dirs = glob.glob(reports_dir)
        for config_dir in config_dirs:
            for file in glob.glob(os.path.join(config_dir, "*.json")):
                with open(file) as f:
                    data = json.load(f)
                    graph_slug = Path(config_dir).stem
                    if graph_slug:
                        try:
                            graph = models.Graph.objects.get(slug=graph_slug)
                            graph.template = editable_report_template
                            graph.save()
                            config, created = ReportConfig.objects.update_or_create(
                                graph=graph,
                                slug=Path(file).stem,
                                defaults={"config": data},
                            )
                            config.clean()
                            print(
                                f'\n\n\tReport config for graph "{graph_slug}" was successfully created'
                            )
                        except ValidationError as e:
                            print(
                                f"\n\n\tReport config at {file} failed to save and was not loaded.\n\tErrors: {e}"
                            )
