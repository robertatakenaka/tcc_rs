import logging

from celery import Celery

from rs.db.data_models import PROC_STATUS_TODO
from rs.utils import response_utils
from rs.core import papers, connections
from rs.configuration import (
    CELERY_BROKER_URL,
    CELERY_RESULT_BACKEND_URL,
    PAPERS_REGISTRATION_QUEUE,
    SOURCES_REGISTRATION_QUEUE,
    LINKS_REGISTRATION_QUEUE,
)


app = Celery('tasks', backend=CELERY_RESULT_BACKEND_URL, broker=CELERY_BROKER_URL)

LOGGER = logging.getLogger(__name__)


def get_queue(registered_paper):
    refs = registered_paper.references
    if len(refs) > 100:
        return 'high_priority'
    if len(refs) > 50:
        return 'default'
    return 'low_priority'


def _handle_result(task_name, result, get_result):
    if get_result:
        return result.get()

    response = response_utils.create_response(task_name)
    response['get_result'] = get_result
    return response


###########################################

def create_paper(network_collection, pid, main_lang, doi, pub_year,
                 uri,
                 subject_areas,
                 paper_titles,
                 abstracts,
                 keywords,
                 references, extra,
                 get_result=None,
                 ):
    print("call task_create_paper")
    res = task_create_paper.apply_async(
        queue=PAPERS_REGISTRATION_QUEUE,
        args=(
            network_collection, pid, main_lang, doi, pub_year,
            uri,
            subject_areas,
            paper_titles,
            abstracts,
            keywords,
            references, extra,
        ),
    )
    return _handle_result("task create_paper", res, get_result)


@app.task()
def task_create_paper(
        network_collection, pid, main_lang, doi, pub_year,
        uri,
        subject_areas,
        paper_titles,
        abstracts,
        keywords,
        references, extra,
        ):
    print("task_create_paper")
    return papers.create_paper(
        network_collection, pid, main_lang, doi, pub_year,
        uri,
        subject_areas,
        paper_titles,
        abstracts,
        keywords,
        references, extra,
    )


###########################################

def update_paper(_id, network_collection, pid, main_lang, doi, pub_year,
                 uri,
                 subject_areas,
                 paper_titles,
                 abstracts,
                 keywords,
                 references, extra,
                 get_result=None,
                 ):
    print("call task_update_paper")
    res = task_update_paper.apply_async(
        queue=PAPERS_REGISTRATION_QUEUE,
        args=(
            _id,
            network_collection, pid, main_lang, doi, pub_year,
            uri,
            subject_areas,
            paper_titles,
            abstracts,
            keywords,
            references, extra,
        ),
    )
    return _handle_result("task update_paper", res, get_result)


@app.task()
def task_update_paper(
        _id,
        network_collection, pid, main_lang, doi, pub_year,
        uri,
        subject_areas,
        paper_titles,
        abstracts,
        keywords,
        references, extra,
        ):
    print("task_update_paper")
    return papers.update_paper(
        _id,
        network_collection, pid, main_lang, doi, pub_year,
        uri,
        subject_areas,
        paper_titles,
        abstracts,
        keywords,
        references, extra,
    )


###########################################
def add_referenced_by_to_source(ref, paper_id, pid, year, subject_areas, get_result=None):
    MARK = PROC_STATUS_TODO
    print("call task_add_referenced_by_to_source", paper_id)
    res = task_add_referenced_by_to_source.apply_async(
        queue=SOURCES_REGISTRATION_QUEUE,
        args=(ref, paper_id, MARK, pid, year, subject_areas)
    )
    return _handle_result("task add_referenced_by_to_source", res, get_result)


@app.task()
def task_add_referenced_by_to_source(ref, paper_id, MARK, pid, year, subject_areas):
    print("task_add_referenced_by_to_source")
    return connections.add_referenced_by_to_source(ref, paper_id, MARK, pid, year, subject_areas)


###########################################

def find_and_create_connections(paper_id, get_result=None):
    print("find_and_create_connections", paper_id)
    res = task_find_and_create_connections.apply_async(
        queue=LINKS_REGISTRATION_QUEUE, args=(paper_id, ))
    return _handle_result(
        "task find_and_create_connections", res, get_result)


@app.task()
def task_find_and_create_connections(paper_id):
    print("task.task_find_and_create_connections")
    return connections.find_and_create_connections(paper_id)
