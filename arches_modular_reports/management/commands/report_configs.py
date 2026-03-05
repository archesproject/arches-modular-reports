import os
import json
import glob
from arches import __version__ as _arches_version
from arches.app.models.system_settings import settings
from arches.app.models import models
from arches_modular_reports.config_generator_registry import get_all
from arches_modular_reports.models import ReportConfig
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _
from packaging.version import Version
from pathlib import Path

arches_version = Version(_arches_version)


class Command(BaseCommand):
    """
    Commands for managing report configurations

    """

    def add_arguments(self, parser):
        parser.add_argument(
            "operation",
            choices=["load", "write", "generate"],
            help='"load", "write", or "generate" (create configs for all registered generators).',
        )

        parser.add_argument(
            "-g",
            "--graph",
            action="store",
            dest="graph",
            default="all",
            help='Graph slug to operate on. Defaults to "all".',
        )

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
            "--overwrite",
            action="store_true",
            dest="overwrite",
            default=False,
            help="Overwrite existing report configs (generate operation only). Prompts for confirmation.",
        )

    def handle(self, *args, **options):
        graph_slug = options["graph"]

        if options["operation"] == "load":
            if options["source"]:
                self.load_report_configs(options["source"], graph_slug=graph_slug)
            elif os.path.exists(os.path.join(settings.APP_ROOT, "report_configs")):
                source = os.path.join(settings.APP_ROOT, "report_configs/**")
                self.load_report_configs(source, graph_slug=graph_slug)

        elif options["operation"] == "write":
            if options["dest"]:
                self.write_report_configs(options["dest"], graph_slug=graph_slug)
            elif os.path.exists(os.path.join(settings.APP_ROOT, "report_configs")):
                dest = os.path.join(settings.APP_ROOT, "report_configs")
                self.write_report_configs(dest=dest, graph_slug=graph_slug)

        elif options["operation"] == "generate":
            self.generate_registered_configs(
                graph_slug=graph_slug,
                overwrite=options["overwrite"],
            )

    def write_report_configs(self, dest, slug=None, graph_slug=None):
        configs = ReportConfig.objects.all()
        if slug:
            configs = configs.filter(slug=slug)
        if graph_slug and graph_slug != "all":
            configs = configs.filter(graph__slug=graph_slug)
        for config in configs:
            if not os.path.exists(os.path.join(dest, config.graph.slug)):
                os.makedirs(os.path.join(dest, config.graph.slug))
            file_path = os.path.join(dest, config.graph.slug, f"{config.slug}.json")
            with open(file_path, "w") as f:
                json.dump(config.config, f, indent=2)

    def generate_registered_configs(self, graph_slug=None, overwrite=False):
        generators = get_all()
        if not generators:
            self.stdout.write("No config generators registered.")
            return

        eligible_graphs = models.GraphModel.objects.filter(
            isresource=True,
            slug__isnull=False,
        ).exclude(pk=settings.SYSTEM_SETTINGS_RESOURCE_MODEL_ID)
        if arches_version >= Version("8.0"):
            eligible_graphs = eligible_graphs.filter(source_identifier=None)

        if graph_slug and graph_slug != "all":
            eligible_graphs = eligible_graphs.filter(slug=graph_slug)
            if not eligible_graphs.exists():
                self.stderr.write(
                    self.style.ERROR(
                        f'No eligible graph found with slug "{graph_slug}".'
                    )
                )
                return

        if overwrite:
            existing_count = ReportConfig.objects.filter(
                graph__in=eligible_graphs,
                slug__in=generators.keys(),
            ).count()
            targeting_all = not graph_slug or graph_slug == "all"
            if targeting_all or existing_count:
                graph_label = "all graphs" if targeting_all else f'graph "{graph_slug}"'
                confirm = input(
                    f"This will overwrite {existing_count} existing config(s) across {graph_label}. Continue? [y/N] "
                )
                if confirm.strip().lower() != "y":
                    self.stdout.write("Aborted.")
                    return

        for graph in eligible_graphs:
            for slug, factory in generators.items():
                if overwrite:
                    _, created = ReportConfig.objects.update_or_create(
                        graph=graph,
                        slug=slug,
                        defaults={"config": factory(graph)},
                    )
                    status = "Created" if created else "Overwritten"
                else:
                    _, created = ReportConfig.objects.get_or_create(
                        graph=graph,
                        slug=slug,
                        defaults={"config": factory(graph)},
                    )
                    status = "Created" if created else "Skipped"
                self.stdout.write(f"\t{status} [{slug}]: {graph.name}")

    def load_report_configs(self, reports_dir, graph_slug=None):
        editable_report_template = models.ReportTemplate.objects.get(
            name="Modular Report Template"
        )
        config_dirs = glob.glob(reports_dir)
        for config_dir in config_dirs:
            dir_graph_slug = Path(config_dir).stem
            if graph_slug and graph_slug != "all" and dir_graph_slug != graph_slug:
                continue
            for file in glob.glob(os.path.join(config_dir, "*.json")):
                with open(file) as f:
                    data = json.load(f)
                    if dir_graph_slug:
                        try:
                            graph = models.Graph.objects.get(slug=dir_graph_slug)
                            graph.template = editable_report_template
                            graph.save()
                            config, created = ReportConfig.objects.update_or_create(
                                graph=graph,
                                slug=Path(file).stem,
                                defaults={"config": data},
                            )
                            config.clean()

                            print(
                                f'\n\n\tReport {Path(file).name} for graph "{dir_graph_slug}" was successfully loaded'
                            )
                        except ValidationError as e:
                            print(
                                f"\n\n\tReport config at {file} failed to save and was not loaded.\n\tErrors: {e}"
                            )
