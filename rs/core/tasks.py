import logging
from celery import Celery
from celery import chain

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
def _find_and_add_linked_papers_lists(paper_id, total_sources, get_result=False):
    print("task._find_and_add_linked_papers_lists")
    res = chain(
            get_linked_ref_sources.s(paper_id, total_sources),
            get_linked_by_refs__papers_ids.s(paper_id, total_sources),
            get_semantic_search_parameters.s(paper_id),
            compare_texts.s(),
            register_linked_papers.s(paper_id),
          )()
    if get_result:
        return res.get()
    print("finished _find_and_add_linked_papers_lists")


@app.task(autoretry_for=(exceptions.MissingRegisteredSources,),
          retry_kwargs={'max_retries': 3, 'countdown': 20})
def get_linked_ref_sources(paper_id, total_sources):
    print("task.get_linked_ref_sources")
    try:
        sources = controller_.get_linked_ref_sources(paper_id)
        found = len(sources)
        if found < total_sources * 0.7:
            raise exceptions.MissingRegisteredSources(
                "Expected %i. Got %i sources" % (total_sources, found))
    except exceptions.MissingRegisteredSources:
        print("Retry get_parameters_for_semantic_search")
        raise
    else:
        print("sources: %i" % found)
        return 1


@app.task()
def get_linked_by_refs__papers_ids(sources, paper_id, total_sources):
    print("task.get_linked_by_refs__papers_ids")
    sources = controller_.get_linked_ref_sources(paper_id)
    print("sources: %i / %i" % (len(sources), total_sources))
    return controller_.get_linked_by_refs__papers_ids(sources, paper_id)


@app.task()
def get_semantic_search_parameters(selected_ids, paper_id):
    print("task.get_semantic_search_parameters", len(selected_ids))
    return controller_.get_semantic_search_parameters(selected_ids, paper_id)


@app.task()
def compare_texts(parameters):
    print("task.compare_texts")
    text = parameters.get("text")
    texts = parameters.get("texts")
    ids = parameters.get("ids")

    if not all([text, texts, ids]):
        return {}

    print((text, ids, texts))
    result = recommender.compare_papers(text, ids, texts)
    print("task.compare_texts: fim")
    print(result)
    result['ids'] = ids
    return result


@app.task()
def register_linked_papers(papers, paper_id):
    print("task.register_linked_papers")
    print((papers, paper_id))
    result = controller_.register_linked_papers(
        paper_id,
        papers.get('recommended'),
        papers.get('rejected'),
        papers.get('ids'),
    )
    print("task.register_linked_papers: fim")
    print(result)
    return result

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
