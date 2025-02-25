from django.core.cache import caches
from django.urls import reverse
from django.utils.translation import gettext as _
from rdflib import Namespace
from rdflib import URIRef
from rdflib import ConjunctiveGraph as Graph
from rdflib.namespace import RDF

from arches.app.models import models
from arches.app.models.system_settings import settings
from arches.app.utils.data_management.resources.formats.rdffile import JsonLdWriter

rdffile_cache = caches["rdffile"]


class JsonLdWriterWithGraphCaching(JsonLdWriter):
    """This is a copy of get_rdf_graph() from core with one change:

    - the graph_cache is now retrieved from the Django cache to be
      reused across requests. The default timeout is 5 minutes and
      can be further configured in settings.
    """

    def get_rdf_graph(self):
        archesproject = Namespace(settings.ARCHES_NAMESPACE_FOR_DATA_EXPORT)
        graph_uri = URIRef(
            archesproject[reverse("graph", args=[self.graph_id]).lstrip("/")]
        )
        self.logger.debug(
            "Using `{0}` for Arches URI namespace".format(
                settings.ARCHES_NAMESPACE_FOR_DATA_EXPORT
            )
        )
        self.logger.debug("Using `{0}` for Graph URI".format(graph_uri))

        g = Graph()
        g.bind("archesproject", archesproject, False)
        # graph_cache = {}
        graph_cache = rdffile_cache.get("graphs", {})

        def get_nodegroup_edges_by_collector_node(node):
            edges = []
            nodegroup = node.nodegroup

            def getchildedges(node):
                for edge in models.Edge.objects.filter(domainnode=node).select_related(
                    "rangenode__nodegroup", "domainnode"
                ):
                    if nodegroup == edge.rangenode.nodegroup:
                        edges.append(edge)
                        getchildedges(edge.rangenode)

            getchildedges(node)
            return edges

        def get_graph_parts(graphid):
            if graphid not in graph_cache:
                graph_cache[graphid] = {
                    "rootedges": [],
                    "subgraphs": {},
                    "nodedatatypes": {},
                }
                graph = (
                    models.GraphModel.objects.filter(pk=graphid)
                    .prefetch_related("node_set__nodegroup")
                    .get()
                )
                nodegroups = set()
                for node in graph.node_set.all():
                    graph_cache[graphid]["nodedatatypes"][
                        str(node.nodeid)
                    ] = node.datatype
                    if node.nodegroup:
                        nodegroups.add(node.nodegroup)
                    if node.istopnode:
                        for edge in get_nodegroup_edges_by_collector_node(node):
                            if edge.rangenode.nodegroup is None:
                                graph_cache[graphid]["rootedges"].append(edge)
                for nodegroup in nodegroups:
                    graph_cache[graphid]["subgraphs"][nodegroup] = {
                        "edges": [],
                        "inedge": None,
                        "parentnode_nodegroup": None,
                    }
                    graph_cache[graphid]["subgraphs"][nodegroup]["inedge"] = (
                        models.Edge.objects.filter(rangenode_id=nodegroup.pk)
                        .select_related("domainnode__nodegroup")
                        .get()
                    )
                    graph_cache[graphid]["subgraphs"][nodegroup][
                        "parentnode_nodegroup"
                    ] = graph_cache[graphid]["subgraphs"][nodegroup][
                        "inedge"
                    ].domainnode.nodegroup
                    graph_cache[graphid]["subgraphs"][nodegroup]["edges"] = (
                        get_nodegroup_edges_by_collector_node(
                            models.Node.objects.filter(pk=nodegroup.pk)
                            .select_related("nodegroup")
                            .get()
                        )
                    )

            rdffile_cache.set("graphs", graph_cache)
            return graph_cache[graphid]

        def add_edge_to_graph(graph, domainnode, rangenode, edge, tile, graph_info):
            pkg = {}
            pkg["d_datatype"] = graph_info["nodedatatypes"].get(str(edge.domainnode_id))
            dom_dt = self.datatype_factory.get_instance(pkg["d_datatype"])
            # Don't process any further if the domain datatype is a literal
            if dom_dt.is_a_literal_in_rdf():
                return

            pkg["r_datatype"] = graph_info["nodedatatypes"].get(str(edge.rangenode_id))
            pkg["range_tile_data"] = None
            pkg["domain_tile_data"] = None
            if str(edge.rangenode_id) in tile.data:
                pkg["range_tile_data"] = tile.data[str(edge.rangenode_id)]
            if str(edge.domainnode_id) in tile.data:
                pkg["domain_tile_data"] = tile.data[str(edge.domainnode_id)]
            elif (
                tile.parenttile is not None
                and str(edge.domainnode_id) in tile.parenttile.data
            ):
                pkg["domain_tile_data"] = tile.parenttile.data[str(edge.domainnode_id)]

            rng_dt = self.datatype_factory.get_instance(pkg["r_datatype"])
            pkg["d_uri"] = dom_dt.get_rdf_uri(domainnode, pkg["domain_tile_data"], "d")
            if rng_dt.collects_multiple_values():
                # If the range datatype collects multiple values, then there is no get
                # the RDF URI for the range node as it unused or looked up later.
                # This saved db queries. re #11572
                pkg["r_uri"] = None
            else:
                pkg["r_uri"] = rng_dt.get_rdf_uri(
                    rangenode, pkg["range_tile_data"], "r"
                )

            # Concept on a node that is not required, but not present
            # Nothing to do here
            if pkg["r_uri"] is None and pkg["range_tile_data"] is None:
                return

            # JSON-LD fails assert if domain node empty while range node has data.
            # Unknown!=Undefined, but reasonable substitution to omit edge from null domain.
            if pkg["d_uri"] is None and pkg["range_tile_data"]:
                self.logger.warning(
                    _(
                        "Unable to return range value because domain is None, re https://github.com/archesproject/arches/pull/9783/files"
                    )
                )
                return

            # FIXME:  Why is this not in datatype.to_rdf()

            # Domain node is NOT a literal value in the RDF representation, so will have a type:
            if type(pkg["d_uri"]) == list:
                for duri in pkg["d_uri"]:
                    graph.add((duri, RDF.type, URIRef(edge.domainnode.ontologyclass)))
            else:
                graph.add(
                    (pkg["d_uri"], RDF.type, URIRef(edge.domainnode.ontologyclass))
                )

            # Use the range node's datatype.to_rdf() method to generate an RDF representation of it
            # and add its triples to the core graph

            # FIXME: some datatypes have their URI calculated from _tile_data (e.g. concept)
            # ... if there is a list of these, then all of the permutations will happen
            # ... as the matrix below re-processes all URIs against all _tile_data entries :(
            if type(pkg["d_uri"]) == list:
                mpkg = pkg.copy()
                for d in pkg["d_uri"]:
                    mpkg["d_uri"] = d
                    if (
                        type(pkg["r_uri"]) == list
                        and not rng_dt.collects_multiple_values()
                    ):
                        npkg = mpkg.copy()
                        for r in pkg["r_uri"]:
                            # compute matrix of n * m
                            npkg["r_uri"] = r
                            graph += rng_dt.to_rdf(npkg, edge)
                    else:
                        # iterate loop on m * 1
                        graph += rng_dt.to_rdf(mpkg, edge)
            elif type(pkg["r_uri"]) == list and not rng_dt.collects_multiple_values():
                npkg = pkg.copy()
                for r in pkg["r_uri"]:
                    # compute matrix of 1 * m
                    npkg["r_uri"] = r
                    graph += rng_dt.to_rdf(npkg, edge)
            else:
                # both are single, 1 * 1
                graph += rng_dt.to_rdf(pkg, edge)

        for resourceinstanceid, tiles in self.resourceinstances.items():
            graph_info = get_graph_parts(self.graph_id)

            # add the edges for the group of nodes that include the root (this group of nodes has no nodegroup)
            for edge in graph_cache[self.graph_id]["rootedges"]:
                domainnode = archesproject[str(edge.domainnode_id)]
                rangenode = archesproject[str(edge.rangenode_id)]
                add_edge_to_graph(g, domainnode, rangenode, edge, None, graph_info)

            for tile in tiles:
                # add all the edges for a given tile/nodegroup
                for edge in graph_info["subgraphs"][tile.nodegroup]["edges"]:
                    domainnode = archesproject[
                        "tile/%s/node/%s" % (str(tile.pk), str(edge.domainnode_id))
                    ]
                    rangenode = archesproject[
                        "tile/%s/node/%s" % (str(tile.pk), str(edge.rangenode_id))
                    ]
                    add_edge_to_graph(g, domainnode, rangenode, edge, tile, graph_info)

                # add the edge from the parent node to this tile's root node
                # where the tile has no parent tile, which means the domain node has no tile_id
                if (
                    graph_info["subgraphs"][tile.nodegroup]["parentnode_nodegroup"]
                    is None
                ):
                    edge = graph_info["subgraphs"][tile.nodegroup]["inedge"]
                    if edge.domainnode.istopnode:
                        domainnode = archesproject[
                            reverse("resources", args=[resourceinstanceid]).lstrip("/")
                        ]
                    else:
                        domainnode = archesproject[str(edge.domainnode_id)]
                    rangenode = archesproject[
                        "tile/%s/node/%s" % (str(tile.pk), str(edge.rangenode_id))
                    ]
                    add_edge_to_graph(g, domainnode, rangenode, edge, tile, graph_info)

                # add the edge from the parent node to this tile's root node
                # where the tile has a parent tile
                if (
                    graph_info["subgraphs"][tile.nodegroup]["parentnode_nodegroup"]
                    is not None
                ):
                    edge = graph_info["subgraphs"][tile.nodegroup]["inedge"]
                    domainnode = archesproject[
                        "tile/%s/node/%s"
                        % (str(tile.parenttile_id), str(edge.domainnode_id))
                    ]
                    rangenode = archesproject[
                        "tile/%s/node/%s" % (str(tile.pk), str(edge.rangenode_id))
                    ]
                    add_edge_to_graph(g, domainnode, rangenode, edge, tile, graph_info)
        return g
