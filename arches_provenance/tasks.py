import logging
from celery import shared_task
from django.contrib.auth.models import User
from django.utils.translation import gettext as _
from arches.app.models import models


@shared_task
def bulk_data_merge_resources(userid, load_id, baseResource, mergeResources):
    from arches_provenance.etl_modules import Resources_merge
    logger = logging.getLogger(__name__)

    try:
        
        BulkPayment = Resources_merge.Resourcesmerge(loadid=load_id)
        BulkPayment.run_load_task(userid, load_id, baseResource, mergeResources)

        load_event = models.LoadEvent.objects.get(loadid=load_id)
        status = _("Completed") if load_event.status == "indexed" else _("Failed")
    except Exception as e:
        logger.error(e)
        load_event = models.LoadEvent.objects.get(loadid=load_id)
        load_event.status = "failed"
        load_event.save()
        status = _("Failed")
    finally:
        msg = _("Bulk Data Edit: {} [{}]").format(status, status)
        user = User.objects.get(id=userid)
        notify_completion(msg, user)


def notify_completion(msg, user, notiftype_name=None, context=None):
    if notiftype_name is not None:
        notif_type = models.NotificationType.objects.get(name=notiftype_name)
    else:
        notif_type = None
    notif = models.Notification.objects.create(notiftype=notif_type, message=msg, context=context)
    models.UserXNotification.objects.create(notif=notif, recipient=user)