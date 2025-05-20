details = {
    "etlmoduleid": "",
    "name": "Merge Resources",
    "description": "Merge two or more resources into one resource",
    "etl_type": "edit",
    "component": "views/components/etl_modules/Resources_merge",
    "componentname": "Resources_merge",
    "modulename": "Resources_merge.py",
    "classname": "Resourcesmerge",
    "config": {"bgColor": "#f5c60a", "circleColor": "#f9dd6c"},
    "icon": "fa fa-upload",
    "slug": "Resources_merge",
    "helpsortorder": 8,
    "helptemplate": "Resources_merge-help",
    "reversible": False

}


from datetime import datetime
import json
import logging
import uuid

from django.db import connection, transaction
import json
from arches.app.models.resource import Resource
from django.contrib.auth.models import User
from django.utils.translation import gettext as _
from arches.app.etl_modules.base_data_editor import BaseBulkEditor
from arches.app.etl_modules.decorators import load_data_async
from arches.app.models.system_settings import settings
from arches.app.utils.index_database import index_resources_by_transaction
import arches.app.utils.task_management as task_management
import arches_provenance.tasks as tasks
logger = logging.getLogger(__name__)

class MissingRequiredInputError(Exception):
    pass

def log_event_details(cursor, loadid, details):
    cursor.execute(
        """UPDATE load_event SET load_description = concat(load_description, %s) WHERE loadid = %s""",
        (details, loadid),
    )

class Resourcesmerge(BaseBulkEditor):
    
    def __init__(self, request=None, loadid=None):
        self.request = request if request else None
        self.userid = request.user.id if request else None
        self.loadid = request.POST.get("load_id") if request else loadid
        self.moduleid = request.POST.get("module") if request else None
        self.node_lookup = {}

    def editor_log(self, cursor, resourceid):
        id = uuid.uuid4()
        cursor.execute(
                """INSERT INTO edit_log (editlogid, resourceinstanceid, edittype, transactionid) VALUES (%s, %s, %s, %s)""",
                (id, resourceid, "tile edit", str(self.loadid)),
            )
        
    def sql_code(self, cursor, sqlQuyre, resourceId):
            
        cursor.execute(sqlQuyre,[str(resourceId)])
        infoResources = cursor.fetchall()
        
        return infoResources

    def check_exist_string_value(self, values, keys):
        flag = True
        i = 0

        for value in values:
            info = json.loads(value[1])

            while flag and i < len(keys):
                val = info.get(keys[i])

                if val is None:
                    i += 1
                    continue

                if isinstance(val, dict):
                    if 'en' in val:
                        flag = False
                        break
                i += 1

        return flag, i

    def check_value_string(self, values, keys):
        flag= True
        i=0
        for value in values:
            info = json.loads(value[1])
            if info=={}:
                return True
            while flag and i < len(keys):
                if info[keys[i]] is None:
                    i +=1
                    continue    
                if 'en' in info[keys[i]]:
                    flag=False
                else:
                    i=i+1
                
        return flag     
    
    def all_list_reference(self, keys, base):
        listReference=[]
        
        info = json.loads(base[1])
        for key in keys:
            if info[key] is None:
                continue
            if isinstance(info[key], list):
                for infoTiledata in info[key]:
                    if 'resourceId' in infoTiledata:
                        listReference.append(infoTiledata['resourceId'])
        return listReference

    def Check_same_information(self, cursor, value, matching_row, keys, order=None, baseId=None):
        info = json.loads(value[1])
       
        if len(matching_row) == 1:
            base=matching_row[0]
            mergeBaseResource = json.loads(base[1])
            # maybe this function have to after loop
            listReference = self.all_list_reference(keys, base)
            FlagDelete=True
            for key in keys:

                if info[key] is None:
                    continue
                if isinstance(info[key], list):
                    for infoTiledata in info[key]:
                        if 'resourceId' in infoTiledata:
                            if infoTiledata['resourceId'] not in listReference:
                                FlagDelete=False
                                if baseId is None:
                                    return True
                                
                                updatevalue = """UPDATE resource_x_resource set resourceinstanceidfrom=%s, tileid=%s where resourcexid=%s ; """
                                cursor.execute(updatevalue, (baseId, base[0], infoTiledata['resourceXresourceId']))
                                mergeBaseResource[key].append(infoTiledata)
                        else:
                            
                            if baseId is None:
                                    return True
                            
                            if infoTiledata not in mergeBaseResource[key]:
                                FlagDelete=False
                                mergeBaseResource[key].append(infoTiledata)
            if baseId is not None:
                if FlagDelete:

                    updatevalue = """UPDATE tiles set resourceinstanceid=%s where tileid=%s ; """
                    cursor.execute(updatevalue, (baseId, base[0]))
                else:
                    deleteXresource = """DELETE FROM resource_x_resource where tileid=%s"""
                    cursor.execute(deleteXresource, (value[0],))
                    delete = """DELETE FROM tiles where tileid=%s"""
                    cursor.execute(delete, (value[0],))
                    updatevalue = """UPDATE  tiles set tiledata=%s where tileid=%s ; """
                    cursor.execute(updatevalue, (json.dumps(mergeBaseResource), base[0]))
        else:
            flag=False

            listReference=[]
            for i, infoTiledata in enumerate(matching_row):
                
                if infoTiledata[1]=='{}':
                    if baseId is None:
                        return False
                    else:
                        flag=True
                else:
                    listReference.extend(self.all_list_reference(keys, infoTiledata))
                    important_value=i
                    if listReference==[]:
                        if baseId is None:
                            return False
                    else:
                        if baseId is None:
                            return True
            
            if info != {}:
                
                mergesTiledata = json.loads(matching_row[important_value][1])
                for resource in info[keys[0]]:
                    if flag:
                        
                        if resource['resourceId'] not in listReference:
                            
                            if baseId is None:
                                return True
                            
                            updatevalue = """UPDATE resource_x_resource set resourceinstanceidfrom=%s, tileid=%s where resourcexid=%s ; """
                            cursor.execute(updatevalue, (baseId, matching_row[important_value][0], resource['resourceXresourceId']))
                            mergesTiledata[keys[0]].append(resource)
                        
                        
                    else:
                        if resource['resourceId'] not in listReference:
                            if baseId is None:
                                return True
                            updatevalue = """UPDATE tiles set resourceinstanceid=%s, sortorder=%s where tileid=%s;"""
                            cursor.execute(updatevalue, (baseId, order, value[0]))
                        
                if flag:
                    updatevalue = """UPDATE  tiles set tiledata=%s where tileid=%s ; """
                    cursor.execute(updatevalue, (json.dumps(mergesTiledata), matching_row[important_value][0]))
        if baseId is None:
            return False
        
    
    def Merge_inforamtion(self, request):
        with connection.cursor() as cursor:
            baseResource = request.POST.get('resourceBase', None)
            mergeResources = request.POST.get('mergeResources', None).split(",")
            checkGraph="SELECT graphid FROM resource_instances WHERE resourceinstanceid=%s "
            checkRresources="SELECT * FROM tiles where resourceinstanceid=%s"
            graphBase = self.sql_code(cursor, checkGraph, baseResource)
            infoResources = self.sql_code(cursor, checkRresources, baseResource)
            if infoResources==[]:
                return{
                    "success": True,
                    'data': {
                        'info': 'No',
                        'info_message': 'There is not this resource:'+baseResource
                    }
                }
            tiledata = "select tileid, tiledata, nodegroupid, parenttileid, sortorder from tiles where resourceinstanceid=%s"
            
            resultBase = self.sql_code(cursor, tiledata, baseResource)
            baseTiles=[]
            for row in resultBase:
                baseTiles.append(list(row))
            AllnodegroupId=[]
            for mergeResource in mergeResources:
                infoResources = self.sql_code(cursor, checkRresources, mergeResource)
                if infoResources==[]:
                    return{
                        "success": True,
                        'data': {
                            'info': 'No',
                            'info_message': 'There is not this resource:'+mergeResource
                        }
                    }
                graphMerge = self.sql_code(cursor, checkGraph, mergeResource)
                
                if graphMerge[0][0] != graphBase[0][0]:
                    return{
                        "success": True,
                        'data': {
                            'info': 'No',
                            'info_message': 'Error for this: '+mergeResource + '. It has different model from integrate resouece'
                        }
                    }
                resultMerge = self.sql_code(cursor, tiledata, mergeResource)
                for mergeTile in resultMerge:
                    matchingNodegroup = [same for same in baseTiles if same[2] == mergeTile[2]]
                    if matchingNodegroup==[]:
                        if mergeTile[2] not in AllnodegroupId:
                            AllnodegroupId.append(mergeTile[2])
                    else:
                        
                        information= json.loads(mergeTile[1])
                        keys = list(information.keys())
                        if matchingNodegroup!={}:
                            flag, i = self.check_exist_string_value(matchingNodegroup,keys)
                            if flag:
                                flagWrite=self.Check_same_information(cursor, mergeTile, matchingNodegroup, keys)
                                if flagWrite and mergeTile[2] not in AllnodegroupId:
                                    AllnodegroupId.append(mergeTile[2])
                            else:
                                if mergeTile[2] not in AllnodegroupId:
                                    AllnodegroupId.append(mergeTile[2])
            nodegroupidList = []
            for nodegroupid in AllnodegroupId:
                
                nameNone = """SELECT c.name FROM nodes n
                inner join cards_x_nodes_x_widgets c_n on n.nodeid=c_n.nodeid
                inner join cards c on c.cardid=c_n.cardid
                where n.nodegroupid=%s """ 

                cursor.execute(nameNone,[str(nodegroupid)])
                infoResources = cursor.fetchall()
                
                if infoResources !=[]:
                    nodegroupidList.append(json.loads(infoResources[0][0])['en'])

            return{
                "success": True,
                'data': {
                    'info': 'Yes',
                    'data': nodegroupidList
                }  
            }
    
    def Child_tile(self, cursor, childtileid ):
        childinfo = """select tileid, tiledata, nodegroupid, parenttileid, sortorder from tiles where tileid=%s """
        mergeInfo = self.sql_code(cursor, childinfo, childtileid)
        return mergeInfo[0]
    
    def update_value(self, cursor, base, value, order, keys):
        updatevalue="""UPDATE tiles set resourceinstanceid=%s, sortorder=%s where tileid=%s;"""
        cursor.execute(updatevalue, (base, order, value[0]))
        nameInfo=json.loads(value[1])
        for key in keys:
            if nameInfo[key] is None:
                continue
            if isinstance(nameInfo[key], list):
                for info in nameInfo[key]:
                    if 'resourceId' in info:
                        updatevalue = """UPDATE resource_x_resource set resourceinstanceidfrom=%s where resourcexid=%s ; """
                        cursor.execute(updatevalue, (base, info['resourceXresourceId']))

    def merge_reference(self,cursor, baseId, valueMerge, base, keys):
        listReference = self.all_list_reference(keys, base)
        flag=False
        valueInfo=json.loads(valueMerge[1])
        baseInfo=json.loads(base[1])
        
        for key in keys:
            if valueInfo[key] is None:
                continue
            if isinstance(valueInfo[key], list):
                for info in valueInfo[key]:
                    if 'resourceId' in info:
                        if info['resourceId'] not in listReference:
                            flag=True
                            updatevalue = """UPDATE resource_x_resource set resourceinstanceidfrom=%s, tileid=%s where resourcexid=%s ; """
                            cursor.execute(updatevalue, (baseId, base[0], info['resourceXresourceId']))
                            baseInfo[key].append(info)
                        else:
                            delete_resource = """DELETE FROM resource_x_resource where resourcexid=%s ; """
                            cursor.execute(delete_resource, (info['resourceXresourceId'],))


        if flag:
            updatevalue = """UPDATE  tiles set tiledata=%s where tileid=%s ; """
            cursor.execute(updatevalue, (json.dumps(baseInfo), base[0]))
    
    def check_information(self, cursor, matching_row, value, keys, base, flagParent, childtileid=None, matching_child=None, childKeys=None):
        findparent = """select tileid from tiles where parenttileid=%s"""
        resultparent = self.sql_code(cursor, findparent, value[0])
        if resultparent !=[] and not flagParent :
            updatevalue = """UPDATE resource_x_resource set resourceinstanceidfrom=%s where tileid=%s ; """
            cursor.execute(updatevalue, (base, value[0]))
            updatevalue = """UPDATE tiles set resourceinstanceid=%s where tileid=%s ; """
            cursor.execute(updatevalue, (base, value[0]))
        else:
            flag, i= self.check_exist_string_value([value], keys)
            info = json.loads(value[1])
            
            if flagParent:
                
                if matching_row==[]:
                    #insert
                    baseInfo= self.Child_tile(cursor, childtileid)
                    self.update_value(cursor, base, baseInfo, 0, childKeys)
                else:
                    if flag:
                        order = 0
                        if matching_child !=[]:
                            order = max(row[-1] for row in matching_child) + 1
                        baseInfo = self.Child_tile(cursor, childtileid)
                        self.update_value(cursor, base, baseInfo, order, childKeys)
                    else:
                        for j, name in enumerate(matching_row):
                            infoName=json.loads(name[1])
                            if infoName[keys[i]] is None:
                                continue
                            if info[keys[i]]['en'] == infoName[keys[i]]['en']:
                                baseInfo = self.Child_tile(cursor, childtileid)
                                for child in matching_child:
                                    if child[-2]==name[0]:
                                        self.merge_reference(cursor, base, baseInfo, child, childKeys)
                                        return None
                        baseInfo = self.Child_tile(cursor, childtileid)
                        order = baseInfo[-1]
                        self.update_value(cursor, base, baseInfo, order, childKeys)

            else:
                
                if matching_row==[]:
                    

                    self.update_value(cursor, base, value, 0, keys)
                else:
                    if flag:
                        
                        order = max(row[-1] for row in matching_row) + 1
                        flafValue=self.check_value_string(matching_row, keys)
                        if flafValue:
                            self.Check_same_information(cursor, value, matching_row, keys, order=order, baseId=base)
                        else:
                            self.update_value(cursor, base, value, order, keys)
                    else:
                        
                        for name in matching_row:
                            nameInfo=json.loads(name[1])
                            if nameInfo[keys[i]] is None:
                                continue
                            if info[keys[i]]['en'] == nameInfo[keys[i]]['en']:
                                self.merge_reference(cursor, base, value, name, keys)
                                return None
                        order = max(row[-1] for row in matching_row) + 1
                        self.update_value(cursor, base, value, order, keys)



    def write(self, request):
        baseResource = request.POST.get('resourceBase', None)
        mergeResources = request.POST.get('mergeResources', None).split(",")
        
        use_celery_bulk_add = True
        load_details = {   
            "baseResource": baseResource,
            "mergeResources": mergeResources
        }
        
        with connection.cursor() as cursor:
            event_created = self.create_load_event(cursor, load_details)
            if event_created["success"]:
                if use_celery_bulk_add:
                    response = self.run_bulk_task_async(request, self.loadid)
                else:
                    response = self.run_bulk_task(self.userid, self.loadid, baseResource, mergeResources)
            else:
                self.log_event(cursor, "failed")
                return {"success": False, "data": event_created["message"]}
        return response 

    @load_data_async
    def run_bulk_task_async(self, request):
        baseResource = request.POST.get('resourceBase', None)
        mergeResources = request.POST.get('mergeResources', None).split(",")

        edit_task = tasks.bulk_data_merge_resources.apply_async(
            (self.userid, self.loadid, baseResource, mergeResources),
        )
        with connection.cursor() as cursor:
            cursor.execute(
                """UPDATE load_event SET taskid = %s WHERE loadid = %s""",
                (edit_task.task_id, self.loadid),
            )
    
    
    @transaction.atomic
    def run_load_task(self, userid, loadid, baseResource, mergeResources):
        
        with connection.cursor() as cursor:
            try:
            
            
                
                self.editor_log(cursor, baseResource)
                tiledataInfo="select tileid, tiledata, nodegroupid, parenttileid, sortorder from tiles where resourceinstanceid=%s order by parenttileid ASC"
                log_event_details(cursor, loadid, "Merge info tiledata...")
                for mergeResource in mergeResources:
                    infoResources = self.sql_code(cursor, tiledataInfo, baseResource)
                    exist=[]
                    for row in infoResources:
                        exist.append(list(row))

                    result = self.sql_code(cursor, tiledataInfo, mergeResource)
                    for row in result:
                        parents=row[3]
                        if parents is None:
                            matching_nodegroup = [same for same in exist if same[2] == row[2]]
                            
                            information= json.loads(row[1])
                            keys = list(information.keys())
                            self.check_information(cursor, matching_nodegroup, row, keys, baseResource, False)
                        else:
                            
                            findTileParent="""select tileid, tiledata, nodegroupid, sortorder from tiles where tileid=%s"""
                            parentInforamion = self.sql_code(cursor, findTileParent, parents)
                            matching_nodegroup_child = [same for same in exist if same[2] == row[2]]
                            information= json.loads(row[1])
                            childKeys = list(information.keys())
                                                
                            for Info in parentInforamion:
                                matching_row = [same for same in exist if same[2] == Info[2]]
                                information= json.loads(Info[1])
                                keys = list(information.keys())
                                self.check_information(cursor, matching_row, Info, keys, baseResource, True, childtileid=row[0], matching_child=matching_nodegroup_child, childKeys=childKeys)
                        
                        selectXResource = "select tileid from resource_x_resource where resourceinstanceidto=%s"
                        tileIds = self.sql_code(cursor, selectXResource, mergeResource)
                        for tileid in tileIds:
                            tiledata="select tiledata from tiles where tileid=%s"
                            infoTile = self.sql_code(cursor, tiledata, tileid[0])
                            
                            infoTiledata = json.loads(infoTile[0][0])
                            
                            keys = list(infoTiledata.keys())
                            for key in keys:
                                
                                if isinstance(infoTiledata[key], list):
                                    for resources in infoTiledata[key]:
                                        if 'resourceId' in resources:
                                            if resources['resourceId']==mergeResource:
                                                resources['resourceId'] = baseResource
                                elif isinstance(infoTiledata[key], dict):
                                    if 'resourceId' in infoTiledata:
                                        if infoTiledata[key]['resourceId']==mergeResource:
                                            infoTiledata['resourceId']=baseResource
                            updatevalue = """UPDATE tiles set tiledata=%s where tileid=%s; """
                            print("second ",infoTiledata)
                            cursor.execute(updatevalue, (json.dumps(infoTiledata), tileid[0]))

                        updatevalue = """UPDATE resource_x_resource set resourceinstanceidto=%s where resourceinstanceidto=%s; """
                        cursor.execute(updatevalue, (baseResource, mergeResource))
                log_event_details(cursor, loadid, "Done|Delete resource...")
                resource = Resource()
                for mergeResource in mergeResources:
                    result = self.sql_code(cursor, tiledataInfo, mergeResource)
                    
                    for row in result:
                        updateold = """UPDATE tiles set tiledata='{}' where tileid=%s ; """
                        cursor.execute(updateold, (row[0],))

                    DeleteResourceXResource = """DELETE FROM resource_x_resource WHERE resourceinstanceidfrom=%s; """
                    cursor.execute(DeleteResourceXResource, (mergeResource,))
                    DeleteGeo="""delete from geojson_geometries where resourceinstanceid=%s"""
                    cursor.execute(DeleteGeo, (mergeResource,))
                    DeleteResourceTiles = """DELETE FROM tiles WHERE resourceinstanceid=%s; """
                    cursor.execute(DeleteResourceTiles, (mergeResource,))
                    DeleteResourceTiles = """DELETE FROM resource_instances WHERE resourceinstanceid=%s; """
                    cursor.execute(DeleteResourceTiles, (mergeResource,))
                    resource.delete_index(mergeResource)
                
                number_of_import = json.dumps({"number_of_import":[{"integrate":1, "merge":len(mergeResources)}]})
                
                cursor.execute("""UPDATE load_event SET (status, load_end_time, load_details) = (%s, %s, load_details || %s::JSONB) WHERE loadid = %s""",
                ("completed", datetime.now(), number_of_import, loadid),)

                log_event_details(cursor, loadid, "done|Indexing...")
                index_resources_by_transaction(loadid, quiet=True, use_multiprocessing=False, recalculate_descriptors=True)

                user = User.objects.get(id=userid)
                user_email = getattr(user, "email", "")
                user_firstname = getattr(user, "first_name", "")
                user_lastname = getattr(user, "last_name", "")
                user_username = getattr(user, "username", "")
                
                cursor.execute(
                    """
                    UPDATE edit_log e
                    SET (resourcedisplayname, userid, user_firstname, user_lastname, user_email, user_username, timestamp) = (r.name ->> %s, %s, %s, %s, %s, %s, %s)
                    FROM resource_instances r
                    WHERE e.resourceinstanceid::uuid = r.resourceinstanceid
                    AND transactionid = %s
                    """,
                    (settings.LANGUAGE_CODE, userid, user_firstname, user_lastname, user_email, user_username, datetime.now(), loadid),
                )
                log_event_details(cursor, loadid, "done")
                cursor.execute(
                    """UPDATE load_event SET (status, indexed_time, complete, successful) = (%s, %s, %s, %s) WHERE loadid = %s""",
                    ("indexed", datetime.now(), True, True, loadid),
                )
                return {"success": True, "data": "done"}
            except Exception as e:
                cursor.execute("""UPDATE load_event SET status = %s, load_end_time = %s WHERE loadid = %s""",
                                ('failed', datetime.now(), self.loadid),)
                self.log_event(cursor, "failed")
                print(_("Unable to edit staged data: {}").format(str(e)))
                return {"success": False, "data": {"title": _("Error"), "message": _("Unable to edit staged data: {}").format(str(e))}}