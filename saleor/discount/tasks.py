from collections import defaultdict
from datetime import datetime

import pytz
from celery.utils.log import get_task_logger

from ..celeryconf import app
from ..plugins.manager import get_plugins_manager
from .models import Sale
from .utils import CATALOGUE_FIELDS, CatalogueInfo

task_logger = get_task_logger(__name__)


def fetch_catalogue_infos(sales):
    catalogue_info: CatalogueInfo = {}
    for sale_data in sales.values("id", *CATALOGUE_FIELDS):
        sale_id = sale_data["id"]
        if sale_id not in catalogue_info:
            catalogue_info[sale_data["id"]] = defaultdict(set)

        for field in CATALOGUE_FIELDS:
            if id := sale_data.get(field):
                catalogue_info[sale_data["id"]][field].add(id)

    return catalogue_info


@app.task
def send_sale_started_and_sale_ended_notifications():
    now = datetime.now(pytz.UTC)
    manager = get_plugins_manager()

    sales_started = Sale.objects.filter(
        started_notification_sent=False, start_date__lte=now
    )
    sales_ended = Sale.objects.filter(ended_notification_sent=False, end_date__lte=now)

    catalogue_infos = fetch_catalogue_infos(sales_started | sales_ended)
    sales_to_update = []

    # send sale_started notifications
    for sale in sales_started:
        catalogues = catalogue_infos.get(sale.id)
        manager.sale_started(sale, catalogues)
        sale.started_notification_sent = True
        sales_to_update.append(sale)

    sales_started_ids = ", ".join([str(sale.id) for sale in sales_started])
    task_logger.info(
        "The sale_started webhook sent for sales with ids: %s", sales_started_ids
    )

    # send sale_ended notifications
    for sale in sales_ended:
        catalogues = catalogue_infos.get(sale.id)
        manager.sale_ended(sale, catalogues)
        sale.ended_notification_sent = True
        sales_to_update.append(sale)

    sales_ended_ids = ", ".join([str(sale.id) for sale in sales_ended])
    task_logger.info(
        "The sale_ended webhook sent for sales with ids: %s", sales_ended_ids
    )

    Sale.objects.bulk_update(
        sales_to_update, ["started_notification_sent", "ended_notification_sent"]
    )
