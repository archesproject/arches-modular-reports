"""
ARCHES - a program developed to inventory and manage immovable cultural heritage.
Copyright (C) 2013 J. Paul Getty Trust and World Monuments Fund

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""


from re import search
from arches.app.models import models
from django.views.generic import View
from arches.app.utils.response import JSONResponse
from arches.app.models.resource import Resource
from arches.app.models.system_settings import settings
from arches.app.models.tile import Tile
from arches.app.utils.label_based_graph_v2 import LabelBasedGraph
from django.db import connection
from arches.app.views.resource import ResourceReportView
from django.shortcuts import render
from arches.app.views.base import BaseManagerView, MapBaseManagerView
from arches.app.views import api
from arches.app.models.graph import Graph

class ProvenanceRelatedResources(View):
    def get(self, request):
        resourceid = request.GET.get("resourceid")
        resourcegraphto = request.GET.get("resourcegraphto")
        offset = request.GET.get("start") if request.GET.get("start") != None else 0
        limit = request.GET.get("length") if request.GET.get("length") != None else  5
        
        
        #get total number of records
        with connection.cursor() as cursor:
            sql = """
            SELECT COUNT(*) FROM resource_x_resource WHERE resourceinstanceidfrom = '{0}' AND resourceinstanceto_graphid = '{1}'
            """.format(resourceid, resourcegraphto)
            cursor.execute(sql)
            records_total = cursor.fetchone()[0]

        sql = """
            SELECT rx.*, r.name->>'en' as name, COUNT(*) OVER() AS full_count 
            FROM resource_x_resource rx
            JOIN resource_instances r on r.resourceinstanceid = rx.resourceinstanceidto WHERE resourceinstanceidfrom = '{0}' AND resourceinstanceto_graphid = '{1}'
            """.format(resourceid, resourcegraphto)
        
        with connection.cursor() as cursor:
            sql = sql + ' OFFSET {0} LIMIT {1}'.format(offset, limit)
            cursor.execute(sql)
            queried_related_resources = cursor.fetchall()

        related_resources = []
        filtered_resources = len(related_resources) 
        for related_resource in queried_related_resources:
            r = {
                'resourcexid': related_resource[0],
                'notes': related_resource[1],
                'datestarted': related_resource[2],
                'dateended': related_resource[3],
                'relationshiptype': related_resource[4],
                'resourceinstancefrom': related_resource[5],
                'resourceinstanceto': related_resource[6],
                'displayname': related_resource[13],
                'modified': related_resource[7],
                'created': related_resource[8],
                'inverserelationshiptype': related_resource[9],
                'tileid': related_resource[10],
                'nodeid': related_resource[11],
                'resourceinstancefrom_graphid': related_resource[12],
                'resourceinstanceto_graphid': related_resource[13],
            }
            filtered_resources=related_resource[14]
            related_resources.append(r)            

        return JSONResponse({'related_resources': related_resources, 'recordsTotal': records_total, 'recordsFiltered': filtered_resources},indent=4)


class ProvenanceSummaryTables(View):
    def get(self, request):
        resourceid = request.GET.get("resourceid")
        nodegroupid = request.GET.get("nodegroupid")
        offset = request.GET.get("start") if request.GET.get("start") != None else 0
        limit = request.GET.get("length") if request.GET.get("length") != None else  5
        search_value = request.GET.get("search[value]") if request.GET.get("search[value]") else None
        nodes = request.GET.get("nodes") if request.GET.get("nodes") != None else ''

        if nodes != '':
            nodes_string = ",".join(['__arches_get_node_display_value(tiledata, \'{0}\'::uuid) AS \"{1}\"'.format(n,n) for n in nodes.split(",")])

        query_string = """
                WITH RECURSIVE
                    children AS ((
                            SELECT 
                                t.tileid,
                                t.tiledata,
                                t.parenttileid,
                                t.nodegroupid,
                                COUNT(*) OVER() AS count,
                                1 AS depth
                            FROM 
                                tiles t
                            WHERE 
                                nodegroupid = '{0}'
                                AND 
                                resourceinstanceid = '{1}'
                             OFFSET {2} LIMIT {3}
                        )
                        UNION
                            SELECT 
                                t.tileid,
                                t.tiledata,
                                t.parenttileid,
                                t.nodegroupid,
                                COUNT(*) OVER() AS count,
                                depth+1
                            FROM 
                                tiles t
                            JOIN children c ON c.tileid = t.parenttileid
                            WHERE depth < 3
                        )
                        SELECT
                            tileid,
                            parenttileid,
                            nodegroupid,
                            count,
                            {4}
                        FROM 
                            children
            """.format(nodegroupid, resourceid, offset, limit, nodes_string)


        if search_value != None:
            search_string = " ".join(['__arches_get_node_display_value(tiledata, \'{0}\'::uuid) ILIKE \'%{1}%\' OR'.format(n, search_value) for n in nodes.split(",")])

            search_string = search_string.rstrip(' OR')

            query_string = query_string + ' WHERE ' + search_string

        #execute query
        with connection.cursor() as cursor:
            sql = query_string + ' OFFSET {0} LIMIT {1}'.format(offset, limit)
            cursor.execute(sql)
            queried_tiles = cursor.fetchall()

        queried_tiles.sort(key=lambda a: str(a[1]))
        queried_tiles = list(queried_tiles)
        
        nodes = ['tileid', 'parenttileid', 'nodegroupid', 'count'] + nodes.split(",")
        tiles = [dict(zip(nodes,tile)) for tile in queried_tiles]
        ret = []

        for t in tiles:
            t['child_nodegroups'] = {}
            if t['parenttileid'] is None:
                ret.append(t)
        
        filtered_tiles = len(ret)
        records_total = ret[0]['count'] if filtered_tiles > 0 else 0

        for t in tiles:
            if t['parenttileid'] is not None:
                for r in ret:
                    if t['parenttileid'] == r['tileid']:
                        if str(t['nodegroupid']) in r['child_nodegroups'].keys():
                            r['child_nodegroups'][str(t['nodegroupid'])].append(t)
                        else:
                            r['child_nodegroups'][str(t['nodegroupid'])] = []
                            r['child_nodegroups'][str(t['nodegroupid'])].append(t)


        for t in tiles:
            if t['parenttileid'] is not None:
                for r in ret:
                    for k,v in r['child_nodegroups'].items():
                        for vv in v:
                            if t['parenttileid'] == vv['tileid']:
                                if str(t['nodegroupid']) in vv['child_nodegroups'].keys():
                                    vv['child_nodegroups'][str(t['nodegroupid'])].append(t)
                                else:
                                    vv['child_nodegroups'][str(t['nodegroupid'])] = []
                                    vv['child_nodegroups'][str(t['nodegroupid'])].append(t)



        return JSONResponse({'data': ret, 'recordsTotal': records_total, 'recordsFiltered': filtered_tiles}, indent=4)     
    
class provenance_report(View):
    def get(self, request):
        resourceid = request.GET.get("resourceid")
        nodegroupid = request.GET.get("nodegroupid")
        tileid = request.GET.get("tileid") if request.GET.get("tileid") != '' else None
        offset = request.GET.get("start") if request.GET.get("start") != None else 0
        limit = request.GET.get("length") if request.GET.get("length") != None else  5
        search_value = request.GET.get("search[value]") if request.GET.get("search[value]") else None
     

        #get total number of records
        with connection.cursor() as cursor:
            sql = """
            SELECT COUNT(*) FROM tiles WHERE nodegroupid = '{0}' AND resourceinstanceid = '{1}'""".format(nodegroupid, resourceid)
            cursor.execute(sql)
            records_total = cursor.fetchone()[0]

        #start query_string
        query_string = "SELECT *, count(*) OVER() AS full_count FROM tiles WHERE nodegroupid = '{0}' AND resourceinstanceid = '{1}'".format(nodegroupid, resourceid)

        if search_value != None:
            query_string = "SELECT q.*, COUNT(*) OVER() AS full_count FROM tiles q JOIN jsonb_each(q.tiledata) d ON true WHERE d.value::text ILIKE '%{0}%' AND nodegroupid = '{1}' AND resourceinstanceid = '{2}'".format(search_value, nodegroupid, resourceid)

        if tileid != None:
            query_string = "SELECT *, count(*) OVER() AS full_count FROM tiles WHERE nodegroupid = '{0}' AND resourceinstanceid = '{1}' AND tileid = '{2}'".format(nodegroupid, resourceid, tileid)

        #execute query
        with connection.cursor() as cursor:
            sql = query_string + ' OFFSET {0} LIMIT {1}'.format(offset, limit)
            cursor.execute(sql)
            queried_tiles = cursor.fetchall()

        #map query results and convert to tile objects
        tiles = []
        filtered_tiles = 0
        for tile in queried_tiles:
            t = {
                'tileid': tile[0],
                'data': tile[1],
                'nodegroup_id': tile[2],
                'parenttileid': tile[3],
                'resourceinstanceid': tile[4],
                'sortorder': tile[5],
                'provisionaledits': tile[6],
            }
            filtered_tiles=tile[7]
            tiles.append(Tile(t))
            
        #perform label based graph lookup
        r = Resource.objects.get(pk=resourceid)
        r.load_tiles()
        lookup = LabelBasedGraph.generate_node_ids_to_tiles_reference_and_nodegroup_cardinality_reference(resource = r)
        
        #gather results for return
        ret = []
        for tile in tiles:
            ret.append(LabelBasedGraph.from_tile(tile, lookup[0], lookup[1]))
        
        return JSONResponse({'data': ret, 'recordsTotal': records_total, 'recordsFiltered': filtered_tiles}, indent=4)
    
class ProvenanceGroupReportView(View):
    def get(self, request, resourceid):
        resource = Resource.objects.get(pk=resourceid)
        graph = Graph.objects.get(graphid=resource.graph_id)
        template = models.ReportTemplate.objects.get(pk=graph.template_id)

        if str(resource.graph_id) == 'd6774bfc-b4b4-11ea-84f7-3af9d3b32b71':
            return JSONResponse({"template": template, "resourceid": resourceid, "resource_name": resource.descriptors['name']})
        else:
            response = api.ResourceReport().get(request, resourceid=resourceid) 
            return response