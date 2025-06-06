import re
from django_hosts import patterns, host

host_patterns = patterns(
    "",
    host(
        re.sub(r"_", r"-", r"arches_modular_reports"),
        "arches_modular_reports.urls",
        name="arches_modular_reports",
    ),
)
