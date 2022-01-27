import logging

from rs.utils import response_utils
from rs.core import tasks, connections

from rs.db import (
    db,
)
from rs.db.data_models import (
    Paper,
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


def get_paper_by_pid(pid):
    return db.get_records(Paper, **{'pid': pid})[0]


def get_paper_by_record_id(_id):
    return db.get_record_by__id(Paper, _id)


def search_papers(text, subject_area, from_year, to_year):
    return connections.search_papers(text, subject_area, from_year, to_year)


def create_paper(network_collection, pid, main_lang, doi, pub_year,
                 uri,
                 subject_areas,
                 paper_titles,
                 abstracts,
                 keywords,
                 references,
                 ):

    response = response_utils.create_response("create_paper")

    # registra o novo documento
    result_create_paper = tasks.create_paper(
            network_collection, pid, main_lang, doi, pub_year,
            uri,
            subject_areas,
            paper_titles,
            abstracts,
            keywords,
            references,
            get_result=True,
        )
    response.update(result_create_paper)

    paper_id = response.get("registered_paper")

    if not paper_id:
        # finaliza se houve erro ao registrar
        return response

    # obtém os dados do documento registrado
    paper = get_paper_by_record_id(paper_id)

    # cria ou atualiza os registros de sources usando os dados das referências
    result = _register_refs_sources(paper)
    response.update(result or {})

    if paper.proc_status == PROC_STATUS_NA:
        # finaliza se paper não tem dados para processar a similaridade
        return response

    result = tasks.find_and_create_connections(paper_id)
    response.update(result or {})
    return response


def update_paper(_id, network_collection, pid, main_lang, doi, pub_year,
                 uri,
                 subject_areas,
                 paper_titles,
                 abstracts,
                 keywords,
                 references,
                 ):

    response = response_utils.create_response("update_paper")

    # registra o novo documento
    result_update_paper = tasks.update_paper(
            _id,
            network_collection, pid, main_lang, doi, pub_year,
            uri,
            subject_areas,
            paper_titles,
            abstracts,
            keywords,
            references,
            get_result=True,
        )
    response.update(result_update_paper)

    paper_id = response.get("registered_paper")

    if not paper_id:
        # finaliza se houve erro ao registrar
        return response

    # obtém os dados do documento registrado
    paper = get_paper_by_record_id(paper_id)

    # cria ou atualiza os registros de sources usando os dados das referências
    result = _register_refs_sources(paper)
    response.update(result or {})

    if paper.proc_status == PROC_STATUS_NA:
        # finaliza se paper não tem dados para processar a similaridade
        return response

    result = tasks.find_and_create_connections(paper_id)
    response.update(result or {})
    return response


def _register_refs_sources(paper):
    response = response_utils.create_response("register_refs_sources")

    if not paper.proc_status == PROC_STATUS_SOURCE_REGISTERED:
        print("register_refs_sources", paper.proc_status)
        return response

    for ref in paper.references:
        if not ref.has_data_enough:
            continue
        try:
            print("call tasks.add_referenced_by_to_source")
            result = tasks.add_referenced_by_to_source(
                ref.as_dict, paper._id,
                paper.pid, paper.pub_year, paper.subject_areas,
                paper.proc_status == PROC_STATUS_SOURCE_REGISTERED,
            )
            print(result)
            if result == PROC_STATUS_TODO:
                paper.proc_status = PROC_STATUS_TODO
                paper.save()

        except Exception as e:
            response_utils.add_error(response, "Unable to create/update source", "")
            response_utils.add_exception(response, e)
    return response


def find_and_create_connections(paper_pid):
    paper = get_paper_by_pid(paper_pid)
    return tasks.find_and_create_connections(paper._id)


def get_connected_papers(pid, min_score=None):
    registered_paper = get_paper_by_pid(pid)
    return registered_paper.get_connections(min_score)
