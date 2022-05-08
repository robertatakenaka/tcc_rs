import logging

from xlingual_papers_recommender.utils import response_utils
from xlingual_papers_recommender.core import tasks, connections, papers

from xlingual_papers_recommender import exceptions
from xlingual_papers_recommender.db.data_models import (
    Journal,
    PROC_STATUS_NA,
    PROC_STATUS_SOURCE_REGISTERED,
    PROC_STATUS_TODO,
)


LOGGER = logging.getLogger(__name__)


# def db_connect(host):
#     try:
#         db.mk_connection(host)
#     except:
#         exit()


def get_subject_areas(journal_issn):
    try:
        journal = Journal.objects(pid=journal_issn)[0]
    except:
        return
    else:
        return journal.subject_areas


def search_papers(text, subject_area, from_year, to_year):
    return connections.search_papers(text, subject_area, from_year, to_year)


def register_paper(network_collection, pid, main_lang, doi, pub_year,
                   uri,
                   subject_areas,
                   paper_titles,
                   abstracts,
                   keywords,
                   references, extra=None, skip_update=False,
                   ):

    response = response_utils.create_response("register_paper")

    if skip_update:
        try:
            paper = papers.get_paper_by_pid(pid)
            response['skip_update'] = True
            return response
        except exceptions.PaperNotFoundError:
            pass

    # registra documento
    result_register_paper = tasks.register_paper(
            network_collection, pid, main_lang, doi, pub_year,
            uri,
            subject_areas,
            paper_titles,
            abstracts,
            keywords,
            references, extra,
            get_result=True,
        )
    response.update(result_register_paper)

    paper = papers.get_paper_by_pid(pid)

    # cria ou atualiza os registros de sources usando os dados das referências
    result = _register_refs_sources(paper)
    response.update(result or {})

    if paper.proc_status == PROC_STATUS_NA:
        # finaliza se paper não tem dados para processar a similaridade
        return response

    result = tasks.find_and_create_connections(paper._id)
    response.update(result or {})
    return response


def _register_refs_sources(paper):
    response = response_utils.create_response("register_refs_sources")

    if not paper.proc_status == PROC_STATUS_SOURCE_REGISTERED:
        return response

    for ref in paper.references:
        if not ref.has_data_enough:
            continue
        try:
            result = tasks.add_referenced_by_to_source(
                ref.as_dict, paper._id,
                paper.pid, paper.pub_year, paper.subject_areas,
                paper.proc_status == PROC_STATUS_SOURCE_REGISTERED,
            )
            if result == PROC_STATUS_TODO:
                paper.proc_status = PROC_STATUS_TODO
                paper.save()

        except Exception as e:
            response_utils.add_error(response, "Unable to create/update source", "")
            response_utils.add_exception(response, e)
    return response


def find_and_create_connections(paper_pid):
    paper = papers.get_paper_by_pid(paper_pid)
    return tasks.find_and_create_connections(paper._id)


def get_connected_papers(pid, min_score=None):
    registered_paper = papers.get_paper_by_pid(pid)
    return registered_paper.get_connections(min_score)
