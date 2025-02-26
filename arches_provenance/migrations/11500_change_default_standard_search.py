from django.db import migrations
from arches.app.models.models import SearchComponent

class Migration(migrations.Migration):
    dependencies = [
    ("arches_provenance", "0001_initial"),
    ]
    def forwards_func(apps, schema_editor):
        search_component=SearchComponent.objects.get(componentname=str('standard-search-view'))
        config=search_component.config
        for info in config['linkedSearchFilters']:
            if info['componentname']=='map-filter':
                info['layoutSortorder']=2
            if info['componentname']=='advanced-search':
                info['layoutSortorder']=1
        search_component.save()
    
    def reverse_func(apps, schema_editor):
        search_component=SearchComponent.objects.get(componentname=str('standard-search-view'))
        config=search_component.config
        for info in config['linkedSearchFilters']:
            if info['componentname']=='map-filter':
                info['layoutSortorder']=1
            if info['componentname']=='advanced-search':
                info['layoutSortorder']=2
        search_component.save()
    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]