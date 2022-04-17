import logging

from celery import Celery

from xlingual_papers_recommender.utils import response_utils
from xlingual_papers_recommender.tools.csv_inputs import csv_inputs_controller
from xlingual_papers_recommender.configuration import (
    CELERY_BROKER_URL,
    CELERY_RESULT_BACKEND_URL,
    REGISTER_ROW_QUEUE,
)


app = Celery('tasks', backend=CELERY_RESULT_BACKEND_URL, broker=CELERY_BROKER_URL)

LOGGER = logging.getLogger(__name__)


def _handle_result(task_name, result, get_result):
    if get_result:
        return result.get()

    response = response_utils.create_response(task_name)
    response['get_result'] = get_result
    return response


###########################################

def register_row(row, get_result=None):
    print("call task_create_row")
    res = task_register_row.apply_async(
        queue=REGISTER_ROW_QUEUE,
        args=(row, ),
    )
    return _handle_result("task create_row", res, get_result)


@app.task()
def task_register_row(row):
    print("task_create_paper")
    return csv_inputs_controller.register_row(row)
