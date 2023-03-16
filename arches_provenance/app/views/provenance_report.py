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


import operator
import json
from re import search
from functools import reduce
from arches.app.models import models
from django.views.generic import View
from arches.app.utils.response import JSONResponse
from arches.app.models.models import CardXNodeXWidget, Node
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
from django.utils import translation
from arches.app.utils.betterJSONSerializer import JSONSerializer
from arches.app.utils.permission_backend import user_is_resource_reviewer

class ProvenanceRelatedResources(View):
    def get(self, request):
        resourceid = request.GET.get("resourceid")
        resourcegraphto = request.GET.get("resourcegraphto")
        offset = request.GET.get("start") if request.GET.get("start") != None else 0
        limit = request.GET.get("length") if request.GET.get("length") != None else  5
        search_value = request.GET.get("search[value]") if request.GET.get("search[value]") else None
        order_column = request.GET.get("columns[{0}][name]".format(int(request.GET.get("order[0][column]")))) if request.GET.get("order[0][column]") != None else "resourceinstanceidto"
        order_dir = request.GET.get("order[0][dir]") if request.GET.get("order[0][column]") != None else "ASC"
        
        #get total number of records
        with connection.cursor() as cursor:
            sql = """
            SELECT COUNT(*) FROM resource_x_resource WHERE resourceinstanceidfrom = '{0}' AND resourceinstanceto_graphid = '{1}'
            """.format(resourceid, resourcegraphto)
            cursor.execute(sql)
            records_total = cursor.fetchone()[0]
        
            #create query to get related resource data
            query_string = """
            WITH relations AS (
                SELECT 
                    rx.*, 
                    r.name->>'en' AS name
                FROM resource_x_resource rx
                JOIN resource_instances r ON rx.resourceinstanceidto = r.resourceinstanceid
                WHERE 
                    rx.resourceinstanceidfrom = '{0}' AND rx.resourceinstanceto_graphid = '{1}'
                UNION 
                SELECT 
                    rx.*, 
                    r.name->>'en' AS name
                FROM resource_x_resource rx
                JOIN resource_instances r ON rx.resourceinstanceidfrom = r.resourceinstanceid
                WHERE 
                    rx.resourceinstanceidto = '{2}' AND rx.resourceinstancefrom_graphid = '{3}'
                )
            SELECT *, COUNT(*) OVER() AS full_count FROM relations
            """.format(resourceid, resourcegraphto, resourceid, resourcegraphto)

        #append search string to query if a search string exists
        if search_value != None:
            search_string = 'name ILIKE \'%{0}%\' OR inverserelationshiptype ILIKE \'%{1}%\''.format(search_value, search_value)

            query_string = query_string + ' WHERE ' + search_string
        
        with connection.cursor() as cursor:
            #append order column and direction if they exist
            if order_column and order_dir:
                query_string = query_string + ' ORDER BY {0} {1}'.format(order_column, order_dir)
            #append offset and limit to query
            query_string = query_string + ' OFFSET {0} LIMIT {1}'.format(offset, limit)
            cursor.execute(query_string)
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
                #rearrange the data so that resourceinstance from is always the resourceid we passed into this function and the resourceinstanceto is the related resource
                'resourceinstancefrom': related_resource[5] if related_resource[5] == resourceid else resourceid,
                'resourceinstanceto': related_resource[6] if related_resource[6] != resourceid else related_resource[5],
                'displayname': related_resource[14],
                'modified': related_resource[7],
                'created': related_resource[8],
                'inverserelationshiptype': related_resource[9],
                'tileid': related_resource[10],
                'nodeid': related_resource[11],
                'resourceinstancefrom_graphid': related_resource[12],
                'resourceinstanceto_graphid': related_resource[13],
                #create resoruceinstance_to object with resource name and resourceid so we can display the name and use the resourceid in the anchor tag in the template
                'resourceinstance_to': {
                    'resourceid': related_resource[5] if str(related_resource[5]) != resourceid else related_resource[6],
                    'displayname': related_resource[14]
                }
            }
            filtered_resources=related_resource[15]
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
        order_column = request.GET.get("columns[{0}][data]".format(int(request.GET.get("order[0][column]")))) if request.GET.get("order[0][column]") != None else None
        order_dir = request.GET.get("order[0][dir]") if request.GET.get("order[0][column]") != None else "ASC"

        #if nodes were passed in create a where statement that can be appended to the subsequent query_string
        if nodes != '':
            nodes_string = "tiledata -> '{}' -> 0 -> 'resourceId' AS relatedresourceid,".format(nodes.split(",")[0])
            nodes_string = nodes_string + ",".join(['__arches_get_node_display_value(tiledata, \'{0}\'::uuid) AS \"{1}\"'.format(n,n) for n in nodes.split(",")])

        #create where statement for search string that can be appended on to the subsueuqne query_string
        search_string = ''
        if search_value != None:
            search_string = " ".join(['__arches_get_node_display_value(tiledata, \'{0}\'::uuid) ILIKE \'%{1}%\' OR '.format(n, search_value) for n in nodes.split(",")])
            search_string = 'AND ' + search_string.rstrip(' OR')

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
                                tiledata,
                                parenttileid,
                                nodegroupid,
                                count,
                                {2}
                            FROM 
                                children
            """.format(nodegroupid, resourceid, nodes_string)

        #execute query
        with connection.cursor() as cursor:
            cursor.execute(query_string)
            queried_tiles = cursor.fetchall()

        #sort queried tiles and convert to list
        queried_tiles.sort(key=lambda a: str(a[1]))
        queried_tiles = list(queried_tiles)
        
        # zip queried tile values together with keys to create dictionaries for each row
        nodes = ['tileid', 'tiledata', 'parenttileid', 'nodegroupid', 'count', 'relatedresourceid'] + nodes.split(",")
        tiles = [dict(zip(nodes,tile)) for tile in queried_tiles]
        
        ret = []
        
        # get related resourceid and name for resource instance link
        for t in tiles:
            related_resource_name = json.loads(t[nodes[6]]) if t[nodes[6]] != '' and t[nodes[6]] is not None else ''
            related_resourceid = json.loads(t['relatedresourceid']) if t['relatedresourceid'] is not None else ''
            t['related_resource'] = {'relatedresourceinstanceid': related_resourceid, 'name': related_resource_name}
            t['child_nodegroups'] = {}
            if t['parenttileid'] is None:
                ret.append(t)

        # compress parent and child tile data together based on matching tileid and parenttileid
        for t in tiles:
            if t['parenttileid'] is not None:
                for r in ret:
                    if t['parenttileid'] == r['tileid']:
                        if str(t['nodegroupid']) in r['child_nodegroups'].keys():
                            r['child_nodegroups'][str(t['nodegroupid'])].append(t)
                        else:
                            r['child_nodegroups'][str(t['nodegroupid'])] = []
                            r['child_nodegroups'][str(t['nodegroupid'])].append(t)

        # compress child tiles and grandchild tiles
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

        #helper function for list comprehension below
        def check_string_or_int(data):
            try:
                data = int(data)
                return 'int'
            except:
                return 'str'

        #helper function for sort below
        def get_item(a, b):
            # get nested value to sort on from list of nested dicts
            sort_value = ''
            if a is not None:
                if isinstance(a, dict):
                    if b in a.keys():
                        sort_value = operator.getitem(a,b)
                        if sort_value != {}:
                            sort_value = sort_value
                elif isinstance(a, list) and len(a) > 0:
                    sort_value = operator.getitem(a, b)
                else:
                    sort_value = ''
            else:
                sort_value = []
            return sort_value
        
        #set records total before applying search string
        records_total = len(ret)
        
        # search over each row for passed in search_string
        if search_string:    
            results = []
            for r in ret:
                if (r[nodes[-1]] is not None and search_value.upper() in r[nodes[-1]].upper()) or (r['child_nodegroups'].values() is not None and search_value.upper() in str(r['child_nodegroups'].values()).upper()) or (r[nodes[-3]] is not None and search_value.upper() in r[nodes[-3]].upper()):
                    results.append(r)
            ret = results

        # apply offset and limit
        ret[int(offset): int(offset) + int(limit): int(limit)]

        filtered_tiles = len(ret)

        #apply sort column and direction
        if order_column and order_dir:
            # create path from data property from javascript columns array
            path = ['' + a + '' if check_string_or_int(a) == 'str' else int(a) for a in order_column.split('.')]
            # sort based on a value in the nested dict
            ret.sort(key=lambda d: reduce(get_item, path, d), reverse=True if order_dir == 'asc' else False)

        return JSONResponse({'data': ret, 'recordsTotal': records_total, 'recordsFiltered': filtered_tiles}, indent=4)     
    
class provenance_report(View):
    def get(self, request):
        resourceid = request.GET.get("resourceid")
        nodegroupid = request.GET.get("nodegroupid")
        tileid = request.GET.get("tileid") if request.GET.get("tileid") != '' else None
        offset = request.GET.get("start") if request.GET.get("start") != None else 0
        limit = request.GET.get("length") if request.GET.get("length") != None else  5
        search_value = request.GET.get("search[value]") if request.GET.get("search[value]") else None
        order_column = request.GET.get("columns[{0}][name]".format(int(request.GET.get("order[0][column]")))) if request.GET.get("order[0][column]") != None else None
        order_dir = request.GET.get("order[0][dir]") if request.GET.get("order[0][column]") != None else None

        #get total number of records
        with connection.cursor() as cursor:
            sql = """
            SELECT COUNT(*) FROM tiles WHERE nodegroupid = '{0}' AND resourceinstanceid = '{1}'""".format(nodegroupid, resourceid)
            cursor.execute(sql)
            records_total = cursor.fetchone()[0]

        #start query_string
        query_string = "SELECT *, count(*) OVER() AS full_count FROM tiles WHERE nodegroupid = '{0}' AND resourceinstanceid = '{1}'".format(nodegroupid, resourceid)

        #create modified search string if search value exists
        if search_value != None:
            query_string = "SELECT q.*, COUNT(*) OVER() AS full_count FROM tiles q JOIN jsonb_each(q.tiledata) d ON true WHERE d.value::text ILIKE '%{0}%' AND nodegroupid = '{1}' AND resourceinstanceid = '{2}'".format(search_value, nodegroupid, resourceid)

        #create modified search string if tileid exists
        if tileid != None:
            query_string = "SELECT *, count(*) OVER() AS full_count FROM tiles WHERE nodegroupid = '{0}' AND resourceinstanceid = '{1}' AND tileid = '{2}'".format(nodegroupid, resourceid, tileid)

        #execute query
        with connection.cursor() as cursor:
            #apply sort column and direction
            if order_column and order_dir:
                query_string = query_string + " ORDER BY tiledata->>'{0}' {1}".format(order_column, order_dir)
            #apply offset and limit
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

class ProvenanceSourceReferences(View):
    #this view was created specifically for source reference table
    def get(self, request):
        resourceid = request.GET.get("resourceid")
        nodegroupid = request.GET.get("nodegroupid")
        tileid = request.GET.get("tileid") if request.GET.get("tileid") != '' else None
        offset = request.GET.get("start") if request.GET.get("start") != None else 0
        limit = request.GET.get("length") if request.GET.get("length") != None else  5
        search_value = request.GET.get("search[value]") if request.GET.get("search[value]") else None
        order_column = request.GET.get("columns[{0}][name]".format(int(request.GET.get("order[0][column]")))) if request.GET.get("order[0][column]") != None else None
        order_dir = request.GET.get("order[0][dir]") if request.GET.get("order[0][column]") != None else None

        #get total number of records
        with connection.cursor() as cursor:
            sql = """
            SELECT jsonb_array_length(tiledata->'{0}') FROM tiles WHERE nodegroupid='{1}' AND resourceinstanceid = '{2}'""".format(nodegroupid, nodegroupid, resourceid)
            cursor.execute(sql)
            records = cursor.fetchone()
            records_total = records[0] if records != None else 0

        #create search string if a search_value exists
        search_string = ''
        if search_value:
            search_string = " WHERE CAST(__arches_get_resourceinstance_label(b::jsonb)::jsonb->'en'->'value' AS text) ILIKE '%{0}%'".format(search_value)

        query_string= """
            SELECT 
                TRIM('"' from CAST(b::jsonb -> 'resourceId' AS text)),
                TRIM('"' from CAST(__arches_get_resourceinstance_label(b::jsonb)::jsonb->'en'->'value' AS text)) as name,
                count(*) OVER() AS full_count
            FROM 
                (SELECT jsonb_array_elements_text(tiledata->'{0}') AS b FROM tiles WHERE nodegroupid = '{1}' AND resourceinstanceid = '{2}') AS b {3}""".format(nodegroupid, nodegroupid, resourceid, search_string)

        with connection.cursor() as cursor:
            #apply sort column and sort order
            if order_column and order_dir:
                query_string = query_string + " ORDER BY {0} {1}".format(order_column, order_dir)
            #apply offset and limit
            sql = query_string + ' OFFSET {0} LIMIT {1}'.format(offset, limit)
            cursor.execute(sql)
            queried_tiles = cursor.fetchall()

        tiles = []
        filtered_tiles = 0

        #create object to container name and resourceid for display and anchor tag in template
        for tile in queried_tiles:
            t = {
                'reference': {
                    'resourceinstanceid': tile[0],
                    'name': tile[1],
                }
            }
            filtered_tiles=tile[2]
            tiles.append(t)
        ret = tiles

        return JSONResponse({'data': ret, 'recordsTotal': records_total, 'recordsFiltered': filtered_tiles}, indent=4)

class ProvenanceGroupReportView(View):
    def get(self, request, resourceid):
        resource = Resource.objects.get(pk=resourceid)
        graph = Graph.objects.get(graphid=resource.graph_id)
        template = models.ReportTemplate.objects.get(pk=graph.template_id)

        if str(resource.graph_id) == 'd6774bfc-b4b4-11ea-84f7-3af9d3b32b71':
            return JSONResponse({"template": template, "resourceid": resourceid, "resource_name": resource.displayname()})
        else:
            response = api.ResourceReport().get(request, resourceid=resourceid) 
            return response

class ProvenanceEditorView(View):
    def get(self, request):
        nodeid = request.GET.get("nodeid")
        tileid = request.GET.get("tileid")
        resourceid = request.GET.get("resourceid")
        nodegroupid = request.GET.get("nodegroupid")
        parenttileid = request.GET.get("parenttileid")
        if nodeid:
            cardwidget = models.CardXNodeXWidget.objects.prefetch_related("widget", "node").get(node_id=nodeid)
            ret = {'cardwidget': cardwidget, 'node': cardwidget.node, 'widget': cardwidget.widget}
        elif tileid or nodegroupid:
            user_is_reviewer = user_is_resource_reviewer(request.user)
            if tileid:
                tile = Tile.objects.get(pk=tileid)
                resourceid = tile.resourceinstance_id
                nodegroupid = tile.nodegroup_id
            elif nodegroupid and resourceid:
                parenttile = Tile.objects.get(pk=parenttileid)
                tile = Tile.get_blank_tile_from_nodegroup_id(nodegroup_id=nodegroupid, resourceid=resourceid, parenttile=parenttile)
                tile.tileid = None
            resource_instance = Resource.objects.get(pk=resourceid)
            graph = resource_instance.graph
            displayname = resource_instance.displayname()

            nodegroups = []
            editable_nodegroups = []
            nodes = graph.node_set.all().select_related("nodegroup")
            for node in nodes:
                if node.is_collector:
                    added = False
                    if request.user.has_perm("write_nodegroup", node.nodegroup):
                        editable_nodegroups.append(node.nodegroup)
                        nodegroups.append(node.nodegroup)
                        added = True
                    if not added and request.user.has_perm("read_nodegroup", node.nodegroup):
                        nodegroups.append(node.nodegroup)

            serialized_graph = None
            if graph.publication:
                user_language = translation.get_language()
                published_graph = models.PublishedGraph.objects.get(publication=graph.publication, language=user_language)
                serialized_graph = published_graph.serialized_graph

            if serialized_graph:
                serialized_cards = serialized_graph["cards"]
                cardwidgets = [
                    widget
                    for widget in models.CardXNodeXWidget.objects.filter(
                        pk__in=[widget_dict["id"] for widget_dict in serialized_graph["widgets"]]
                    )
                ]
            else:
                cards = graph.cardmodel_set.order_by("sortorder").filter(nodegroup__in=nodegroups).prefetch_related("cardxnodexwidget_set")
                serialized_cards = JSONSerializer().serializeToPython(cards)
                cardwidgets = [widget for widget in [card.cardxnodexwidget_set.order_by("sortorder").all() for card in cards]]

            editable_nodegroup_ids = [str(nodegroup.pk) for nodegroup in editable_nodegroups]
            for card in serialized_cards:
                card["is_writable"] = False
                if str(card["nodegroup_id"]) in editable_nodegroup_ids:
                    card["is_writable"] = True

            ret = {
                "resourceid": resourceid,
                "displayname": displayname,
                "tile": tile,
                "cards": serialized_cards,
                "nodegroups": nodegroups,
                "nodes": nodes.filter(nodegroup__in=nodegroups),
                "cardwidgets": cardwidgets,
                "datatypes": models.DDataType.objects.all(),
                "userisreviewer": user_is_reviewer,
                "widgets": models.Widget.objects.all(),
                "card_components": models.CardComponent.objects.all(),
            }

        return JSONResponse(ret)
