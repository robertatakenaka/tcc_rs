import logging
from celery import Celery

from rs.core import controller_
from rs import exceptions
from rs.core import recommender
from rs.configuration import DATABASE_CONNECT_URL, CELERY_BROKER_URL, CELERY_RESULT_BACKEND_URL


app = Celery('tasks', backend=CELERY_RESULT_BACKEND_URL, broker=CELERY_BROKER_URL)

LOGGER = logging.getLogger(__name__)

controller_._db_connect(DATABASE_CONNECT_URL)


@app.task()
def add_referenced_by_to_source(ref, paper_id):
    # _db_connect(DATABASE_CONNECT_URL)
    print("In task.add_referenced_by_to_source")
    try:
        page = 1
        items_per_page = 100
        order_by = None
        sources = controller_.search_sources(
            ref['doi'], ref['pub_year'],
            ref['surname'], ref['organization_author'],
            ref['source'], ref['journal'], ref['vol'],
            items_per_page, page, order_by,
        )
    except exceptions.InsuficientArgumentsToSearchDocumentError as e:
        LOGGER.info("InsuficientArgumentsToSearchDocumentError")
        LOGGER.info(e)
        return
    try:
        _source = sources[0]
        LOGGER.info("Recuperou")
    except (IndexError, TypeError, ValueError) as e:
        _source = controller_.create_source(**ref)
        LOGGER.info("Criou")

    try:
        _source.add_referenced_by(paper_id)
        LOGGER.info(paper_id)

        _source.save()
        LOGGER.info("source saved")
    except Exception as e:
        LOGGER.info("source not saved")
        LOGGER.info(e)
    LOGGER.info("added reference ...........................")


@app.task()
def compare_texts_and_register_result(paper_id, text, ids, texts):
    papers = recommender.compare_papers(text, ids, texts)
    result = controller_.register_linked_papers(
        paper_id,
        papers.get('recommended'),
        papers.get('rejected'),
        ids,
    )
    LOGGER.info(result)
    return result


# @app.task()
# def compare_texts(text, ids, texts):
#     print("task.compare_texts")
#     print((text, ids, texts))
#     result = recommender.compare_papers(text, ids, texts)
#     print("task.compare_texts: fim")
#     print(result)
#     return result


# @app.task()
# def register_related_papers(papers, paper_id, ids):
#     print("task.register_related_papers")
#     print((papers, paper_id, ids))
#     result = controller_.register_related_papers(
#         paper_id,
#         papers.get('recommended'),
#         papers.get('rejected'),
#         ids,
#     )
#     print("task.register_related_papers: fim")
#     print(result)
#     return result


# @app.task
# def register_related_papers(papers, paper_id, ids):
#     print("register_related_papers: ", paper_id)
#     result = controller_.register_related_papers(
#         paper_id,
#         papers.get('recommended'),
#         papers.get('rejected'),
#         ids,
#     )
#     print("finished register_related_papers")
#     return result
