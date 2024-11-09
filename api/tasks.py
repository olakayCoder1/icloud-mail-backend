import logging, time
from datetime import datetime
from celery import shared_task
from celery.contrib.abortable import AbortableTask
from .icloud.manager import ICloudManager

logger = logging.getLogger(__name__)


@shared_task(bind=True, base=AbortableTask)
def backgroud_email_sending_via_icloud_webmail(self,data):
    time.sleep(10)
    ICloudManager().send_icloud_mail(data)
    print(f"SCHEDULE TASK CALLED {data} :::: {datetime.now()}")

