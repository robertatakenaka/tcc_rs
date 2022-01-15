import logging
from celery import Celery
from celery import chain

from rs.db import data_models

from rs.core import paper_controller, controller_
from rs import exceptions
from rs.core import recommender
from rs.configuration import (
    DATABASE_CONNECT_URL,
    CELERY_BROKER_URL,
    CELERY_RESULT_BACKEND_URL,
)


app = Celery('tasks', backend=CELERY_RESULT_BACKEND_URL, broker=CELERY_BROKER_URL)

LOGGER = logging.getLogger(__name__)

controller_._db_connect(DATABASE_CONNECT_URL)


def get_queue(registered_paper):
    refs = registered_paper.references
    if len(refs) > 100:
        return 'high_priority'
    if len(refs) > 50:
        return 'default'
    return 'low_priority'


###########################################

def receive_new_paper(paper_data, ignore_result=False):
    """
    Cria paper
    Adiciona as recomendações e outros relacionamentos
    """
    try:
        print("Receive new paper")
        response = controller.create_paper(**paper_data)
    except Exception as e:
        print(e)
        return exceptions.add_exception({
            "error": "Unable to register paper",
            "paper": paper_data},
            e,
        )
    else:
        res = None
        # registered_paper = response.get("registered_paper")
        # total_sources = response.get("total sources")
        # print("response", response)
        # if total_sources:
        #     # adiciona links
        #     print("Find and add linked papers")
        #     res = _find_and_add_linked_papers_lists(
        #         registered_paper, ignore_result)
        return {"linked_paper": "created", "result": res}


@app.task()
def task_receive_new_paper(paper_data):
    print("task_receive_new_paper")
    try:
        return paper_controller.create_paper(**paper_data)
    except Exception as e:
        return exceptions.add_exception({
            "error": "Unable to register paper",
            "paper": paper_data},
            e,
        )

###########################################

def add_referenced_by_to_source(ref, paper):
    paper_id = paper._id

    MARK = data_models.PROC_STATUS_TODO
    print("task_add_referenced_by_to_source", paper_id)
    res = task_add_referenced_by_to_source.apply_async(
        queue='low_priority', args=(ref, paper_id, MARK)
    )

    if paper.proc_status:
        return {"msg": "called add_references_to_paper"}

    result = res.get()
    if result == MARK:
        paper.proc_status = MARK


@app.task()
def task_add_referenced_by_to_source(ref, paper_id, MARK):
    print("task_add_referenced_by_to_source")
    return controller_.add_referenced_by_to_source(ref, paper_id, MARK)


###########################################

def _find_and_add_linked_papers_lists(registered_paper, ignore_result=False):
    paper_id = registered_paper._id
    print("_find_and_add_linked_papers_lists", paper_id)
    res = task_find_and_add_linked_papers_lists.apply_async(
        queue=get_queue(registered_paper), args=(paper_id, ))
    if ignore_result:
        return {"msg": "called _find_and_add_linked_papers_lists"}
    return res.get()


@app.task()
def task_find_and_add_linked_papers_lists(paper_id):
    print("task.task_find_and_add_linked_papers_lists")
    ids = controller_.get_linked_by_refs__papers_ids(paper_id)
    if not ids:
        return {"error": "There is no `ids`"}

    parameters = controller_.get_semantic_search_parameters(ids, paper_id)
    if not parameters:
        return {"error": "There is no `parameters`"}

    papers = recommender.compare_papers(**parameters)
    if not papers:
        return {}

    papers['ids'] = ids
    print(papers)
    return controller_.register_linked_papers(
        paper_id,
        papers.get('recommended'),
        papers.get('rejected'),
        papers.get('ids'),
    )


##########################################
# def chained_find_and_add_linked_papers_lists(paper_id):
#     print("_find_and_add_linked_papers_lists", paper_id)
#     x = chain(
#             get_linked_by_refs__papers_ids.s(paper_id),
#             get_semantic_search_parameters.s(paper_id),
#             compare_texts.s(),
#             register_linked_papers.s(paper_id),
#           )
#     res = x()
#     print("finished _find_and_add_linked_papers_lists")
#     return res


# @app.task()
# def get_linked_by_refs__papers_ids(paper_id):
#     print("task.get_linked_by_refs__papers_ids")
#     return ["61e1968dfd981ac846548181"]
#     return controller_.get_linked_by_refs__papers_ids(paper_id)


# @app.task()
# def get_semantic_search_parameters(selected_ids, paper_id):
#     print("task.get_semantic_search_parameters", len(selected_ids))
#     return {"text": "É um resumo", "texts": ["É um resumo"], "ids": ["61e1968dfd981ac846548181"]}
#     if not selected_ids:
#         return {}
#     return controller_.get_semantic_search_parameters(selected_ids, paper_id)


# @app.task()
# def compare_texts(parameters):
#     print("task.compare_texts")
#     text = parameters.get("text")
#     texts = parameters.get("texts")
#     ids = parameters.get("ids")

#     if not all([text, texts, ids]):
#         return {}

#     print((text, ids, texts))
#     result = recommender.compare_papers(text, ids, texts)
#     print("task.compare_texts: fim")
#     print(result)
#     result['ids'] = ids
#     return result


# @app.task()
# def register_linked_papers(papers, paper_id):
#     print("task.register_linked_papers")
#     print((papers, paper_id))

#     if not papers:
#         return {}

#     result = controller_.register_linked_papers(
#         paper_id,
#         papers.get('recommended'),
#         papers.get('rejected'),
#         papers.get('ids'),
#     )
#     print("task.register_linked_papers: fim")
#     print(result)
#     return result

# @app.task()
# def compare_texts_and_register_result(paper_id, text, ids, texts):
#     print("In compare_texts_and_register_result")
#     papers = recommender.compare_papers(text, ids, texts)
#     result = controller_.register_linked_papers(
#         paper_id,
#         papers.get('recommended'),
#         papers.get('rejected'),
#         ids,
#     )
#     LOGGER.info(result)
#     print(result)
#     return result
