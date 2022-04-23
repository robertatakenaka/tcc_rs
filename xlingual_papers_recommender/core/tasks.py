import logging

from celery import Celery

from xlingual_papers_recommender.db.data_models import PROC_STATUS_TODO
from xlingual_papers_recommender.utils import response_utils
from xlingual_papers_recommender.core import papers, connections, recommender
from xlingual_papers_recommender.configuration import (
    CELERY_BROKER_URL,
    CELERY_RESULT_BACKEND_URL,
    PAPERS_REGISTRATION_QUEUE,
    SOURCES_REGISTRATION_QUEUE,
    LINKS_REGISTRATION_QUEUE,
    PAPERS_GET_QUEUE,
    GET_IDS_CONNECTED_BY_REFERENCES_QUEUE,
    GET_SEMANTIC_SEARCH_PARAMETERS_QUEUE,
    COMPARE_PAPERS_QUEUE,
    REGISTER_PAPERS_CONNECTIONS_QUEUE,
    ADD_CONNECTION_QUEUE,
    REGISTER_ROW_QUEUE,
    JOIN_CSV_QUEUE,
    REGISTER_JSON_QUEUE,
    REGISTER_PAPER_QUEUE,
)
from xlingual_papers_recommender.tools.csv_inputs import csv_inputs_controller


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
    # # print("task_create_paper")
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
    # print("call task_update_paper")
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
    # # print("task_update_paper")
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
    # print("call task_add_referenced_by_to_source", paper_id)
    res = task_add_referenced_by_to_source.apply_async(
        queue=SOURCES_REGISTRATION_QUEUE,
        args=(ref, paper_id, MARK, pid, year, subject_areas)
    )
    return _handle_result("task add_referenced_by_to_source", res, get_result)


@app.task()
def task_add_referenced_by_to_source(ref, paper_id, MARK, pid, year, subject_areas):
    # # print("task_add_referenced_by_to_source")
    return connections.add_referenced_by_to_source(ref, paper_id, MARK, pid, year, subject_areas)


###########################################

# def find_and_create_connections(paper_id, get_result=None):
#     # print("find_and_create_connections", paper_id)
#     res = task_find_and_create_connections.apply_async(
#         queue=LINKS_REGISTRATION_QUEUE, args=(paper_id, ))
#     return _handle_result(
#         "task find_and_create_connections", res, get_result)


# @app.task()
# def task_find_and_create_connections(paper_id):
#     # # print("task.task_find_and_create_connections")
#     return connections.find_and_create_connections(paper_id)


def find_and_create_connections(paper_id, get_result=None):
    response = response_utils.create_response("find_and_create_connections")
    paper_data = get_parameters_to_get_ids_connected_by_references(
        paper_id, get_result=True
    )
    if not paper_data:
        response_utils.add_result(
            response, "Do nothing. Paper status is not PROC_STATUS_TODO")
        return response

    paper_data['get_result'] = True
    ids = get_ids_connected_by_references(**paper_data)
    if not ids:
        response_utils.add_result(response, "There is no `ids` to make links")
        return response

    parameters = get_semantic_search_parameters(ids, paper_id, get_result=True)
    if not parameters:
        response_utils.add_result(
            response, "There is no `parameters` to make links")
        return response

    parameters['get_result'] = True
    papers = compare_papers(**parameters)
    if not papers:
        response_utils.add_result(response, "Not found paper links")
        return response

    for evaluated_paper in papers['evaluated']:
        add_connection_by_semantic_similarity(
            evaluated_paper['paper_id'], paper_id, evaluated_paper['score'],
        )

    result = register_papers_connections(
        paper_id,
        papers['evaluated'],
        papers['cut'],
        get_result=get_result,
    )

    return result

###########################################


def add_connection_by_semantic_similarity(paper_id, connected_paper_id, score, get_result=None):
    # print("add_connection_by_semantic_similarity", paper_id)
    res = task_add_connection_by_semantic_similarity.apply_async(
        queue=ADD_CONNECTION_QUEUE,
        args=(paper_id, connected_paper_id, score))
    return _handle_result(
        "task add_connection_by_semantic_similarity", res, get_result)


@app.task()
def task_add_connection_by_semantic_similarity(paper_id, connected_paper_id, score):
    # # print("task.task_add_connection_by_semantic_similarity")
    return papers.add_connection_by_semantic_similarity(
        paper_id, connected_paper_id, score)


###########################################


def register_papers_connections(paper_id, evaluated_papers, cut_papers, get_result=None):
    # print("register_papers_connections", paper_id)
    res = task_register_papers_connections.apply_async(
        queue=REGISTER_PAPERS_CONNECTIONS_QUEUE,
        args=(paper_id, evaluated_papers, cut_papers))
    return _handle_result(
        "task register_papers_connections", res, get_result)


@app.task()
def task_register_papers_connections(paper_id, evaluated_papers, cut_papers):
    # # print("task.task_register_papers_connections")
    return connections.register_papers_connections(
        paper_id, evaluated_papers, cut_papers)
###########################################


def get_parameters_to_get_ids_connected_by_references(paper_id, get_result=None):
    # print("get_parameters_to_get_ids_connected_by_references", paper_id)
    res = task_get_parameters_to_get_ids_connected_by_references.apply_async(
        queue=PAPERS_GET_QUEUE, args=(paper_id, ))
    return _handle_result(
        "task get_parameters_to_get_ids_connected_by_references",
        res, get_result)


@app.task()
def task_get_parameters_to_get_ids_connected_by_references(paper_id):
    # # print("task.task_get_parameters_to_get_ids_connected_by_references")
    return papers.get_parameters_to_get_ids_connected_by_references(paper_id)

###########################################


def get_ids_connected_by_references(paper_id, subject_areas=None,
                                    from_year=None, to_year=None,
                                    get_result=None):
    # print("get_ids_connected_by_references", paper_id)
    res = task_get_ids_connected_by_references.apply_async(
        queue=GET_IDS_CONNECTED_BY_REFERENCES_QUEUE,
        args=(paper_id, subject_areas, from_year, to_year, )
    )
    return _handle_result(
        "task get_ids_connected_by_references", res, get_result)


@app.task()
def task_get_ids_connected_by_references(paper_id, subject_areas=None,
                                         from_year=None, to_year=None):
    # # print("task.task_get_ids_connected_by_references")
    return connections.get_ids_connected_by_references(
        paper_id, subject_areas, from_year, to_year)

###########################################


def get_semantic_search_parameters(ids, paper_id, get_result=None):
    # print("get_semantic_search_parameters", paper_id)
    res = task_get_semantic_search_parameters.apply_async(
        queue=GET_SEMANTIC_SEARCH_PARAMETERS_QUEUE,
        args=(ids, paper_id)
    )
    return _handle_result(
        "task get_semantic_search_parameters", res, get_result)


@app.task()
def task_get_semantic_search_parameters(ids, paper_id):
    # # print("task.task_get_semantic_search_parameters")
    return connections.get_semantic_search_parameters(ids, paper_id)


###########################################


def compare_papers(text, ids, texts, get_result=None):
    # print("compare_papers")
    res = task_compare_papers.apply_async(
        queue=COMPARE_PAPERS_QUEUE,
        args=(text, ids, texts)
    )
    return _handle_result(
        "task compare_papers", res, get_result)


@app.task()
def task_compare_papers(text, ids, texts):
    # # print("task.task_compare_papers")
    return recommender.compare_papers(text, ids, texts)


###########################################

def register_csv_row_data(row, skip_update=False, get_result=None):
    res = task_register_csv_row_data.apply_async(
        queue=REGISTER_ROW_QUEUE,
        args=(row, skip_update),
    )
    return _handle_result("task_register_csv_row_data", res, get_result)


@app.task()
def task_register_csv_row_data(row, skip_update):
    return csv_inputs_controller.register_row(row, skip_update)


###########################################


def csv_rows_to_json(pid, split=False, get_result=None):
    response = _merge_csv(pid, split, get_result=True)
    try:
        papers = response["papers"]
    except KeyError:
        # nao obteve os dados
        return response

    resps = []
    pids = []

    for paper in papers:
        resp = _register_json(paper, get_result)
        pids.append(paper['pid'])
        resps.append(resp)

    response['resps'] = resps
    response['pids'] = pids

    return response


def _merge_csv(pid, split, get_result=None):
    res = task__merge_csv.apply_async(
        queue=JOIN_CSV_QUEUE,
        args=(pid, split),
    )
    return _handle_result("task__merge_csv", res, get_result)


@app.task()
def task__merge_csv(pid, split):
    return csv_inputs_controller.merge_csv(pid, split)


def _register_json(paper_json, get_result=None):
    res = task__register_json.apply_async(
        queue=REGISTER_JSON_QUEUE,
        args=(paper_json, ),
    )
    return _handle_result("task__register_json", res, get_result)


@app.task()
def task__register_json(paper_json):
    return csv_inputs_controller.register_paper_data_as_json(paper_json)


def _fix_args_to_create_paper(data):
    return dict(
        network_collection=data.get('collection'),
        pid=data['pid'],
        main_lang=data.get("main_lang") or data.get("lang") or '',
        doi=data.get("doi"),
        pub_year=data['pid'][10:14],
        uri=data.get("uri") or '',
        subject_areas=list(set(data.get("subject_areas") or [])),
        paper_titles=data.get("paper_titles") or [],
        abstracts=data.get("abstracts") or [],
        keywords=data.get("keywords") or [],
        references=data.get("references") or [],
        extra=data.get("extra"),
        get_result=data.get("get_result"),
    )
