import re
from django_hosts import patterns, host

host_patterns = patterns(
    "",
    host(re.sub(r"_", r"-", r"arches_provenance"), "arches_provenance.urls", name="arches_provenance"),
)
