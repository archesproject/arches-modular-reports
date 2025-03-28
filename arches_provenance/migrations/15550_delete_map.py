from django.db import migrations
from arches.app.models.models import SearchComponent


class Migration(migrations.Migration):
    dependencies = [
        ("arches_provenance", "11500_change_default_standard_search"),
    ]
    def forwards_func(apps, schema_editor):
        try:
            search_component = SearchComponent.objects.get(componentname="standard-search-view")
        except SearchComponent.DoesNotExist:
            return 
        
        config = search_component.config
        filters = config.get("linkedSearchFilters", [])
        
        map_sortorder = None
        for info in filters:
            if info["componentname"] == "map-filter":
                map_sortorder = info["layoutSortorder"]
                break
        
        if map_sortorder is not None:
            config["linkedSearchFilters"] = [
                info for info in filters if info["componentname"] != "map-filter"
            ]
            
            # for info in config["linkedSearchFilters"]:
            #     if info["layoutSortorder"] > map_sortorder:
            #         info["layoutSortorder"] -= 1
            
            search_component.config = config
            search_component.save()

    def reverse_func(apps, schema_editor):
        try:
            search_component = SearchComponent.objects.get(componentname="standard-search-view")
        except SearchComponent.DoesNotExist:
            return
        
        config = search_component.config
        filters = config.get("linkedSearchFilters", [])
        
        map_filter = {
            "componentname": "map-filter",
            "layoutSortorder": 2,
            "searchcomponentid": "09d97fc6-8c83-4319-9cef-3aaa08c3fbec"
        }
        
        for info in filters:
            if info["layoutSortorder"] >= map_filter["layoutSortorder"]:
                info["layoutSortorder"] += 1
        
        filters.append(map_filter)
        filters.sort(key=lambda x: x["layoutSortorder"])
        
        config["linkedSearchFilters"] = filters
        search_component.config = config
        search_component.save()

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]