import logging

from rs.utils import response_utils
from rs.core import tasks
from rs import exceptions
from rs import configuration
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


def db_connect(host):
    try:
        db.mk_connection(host)
    except:
        exit()


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


def search_papers(text, subject_area,
                  begin_year, end_year,
                  items_per_page, page, order_by,
                  ):
    if not text:
        raise exceptions.InsuficientArgumentsToSearchDocumentError(
            "papers_selection.search_papers requires text parameter"
        )
    values = [subject_area, begin_year, end_year, ]
    field_names = [
        'subject_areas',
        'pub_year__gte',
        'pub_year__lte',
    ]
    kwargs = {
        k: v
        for k, v in zip(field_names, values)
        if v
    }
    return Paper.objects(**kwargs).search_text(text).order_by('$text_score')


def create_paper(network_collection, pid, main_lang, doi, pub_year,
                 subject_areas,
                 paper_titles,
                 abstracts,
                 keywords,
                 references,
                 create_sources,
                 create_links,
                 ):

    get_result = create_sources
    response = response_utils.create_response("create_paper")

    # registra o novo documento
    result_create_paper = tasks.create_paper(
            network_collection, pid, main_lang, doi, pub_year,
            subject_areas,
            paper_titles,
            abstracts,
            keywords,
            references,
            get_result,
        )
    response.update(result_create_paper)

    paper_id = response.get("registered_paper")

    if not create_sources or not paper_id:
        # finaliza se a opção create_sources == False ou
        # se houve erro ao registrar
        return response

    # obtém os dados do documento registrado
    paper = get_paper_by_record_id(paper_id)

    # cria ou atualiza os registros de sources usando os dados das referências
    result = register_refs_sources(paper)
    response.update(result or {})

    if not create_links or paper.proc_status == PROC_STATUS_NA:
        # finaliza se a opção create_links == False ou
        # se paper não tem dados para processar a similaridade
        return response

    result = tasks.find_and_add_linked_papers_lists(paper_id)
    response.update(result or {})
    return response


def update_paper(network_collection, pid, main_lang, doi, pub_year,
                 subject_areas,
                 paper_titles,
                 abstracts,
                 keywords,
                 references,
                 create_sources,
                 create_links,
                 ):

    get_result = create_sources
    response = response_utils.create_response("update_paper")

    # registra o novo documento
    result_update_paper = tasks.update_paper(
            network_collection, pid, main_lang, doi, pub_year,
            subject_areas,
            paper_titles,
            abstracts,
            keywords,
            references,
            get_result,
        )
    response.update(result_update_paper)

    paper_id = response.get("registered_paper")

    if not create_sources or not paper_id:
        # finaliza se a opção create_sources == False ou
        # se houve erro ao registrar
        return response

    # obtém os dados do documento registrado
    paper = get_paper_by_record_id(paper_id)

    # cria ou atualiza os registros de sources usando os dados das referências
    result = register_refs_sources(paper)
    response.update(result or {})

    if not create_links or paper.proc_status == PROC_STATUS_NA:
        # finaliza se a opção create_links == False ou
        # se paper não tem dados para processar a similaridade
        return response

    result = tasks.find_and_add_linked_papers_lists(paper_id)
    response.update(result or {})
    return response


def register_refs_sources(paper):
    try:
        print("register_refs_sources", paper.proc_status)
        if paper.proc_status == PROC_STATUS_SOURCE_REGISTERED:
            for ref in paper.references:
                if ref.has_data_enough:
                    print("call tasks.add_referenced_by_to_source")
                    result = tasks.add_referenced_by_to_source(
                        ref.as_dict, paper._id,
                        paper.proc_status == PROC_STATUS_SOURCE_REGISTERED)
                    print(result)
                    if result == PROC_STATUS_TODO:
                        paper.proc_status = PROC_STATUS_TODO
                        paper.save()

    except Exception as e:
        response = response_utils.create_response("register_refs_sources")
        response_utils.add_error(response, "Unable to create/update source", "")
        response_utils.add_exception(response, e)
        return response


def find_and_add_linked_papers_lists(paper_pid):
    paper = get_paper_by_pid(paper_pid)
    return tasks.find_and_add_linked_papers_lists(paper._id)


def get_linked_papers_lists(pid):
    registered_paper = get_paper_by_pid(pid)
    lists = registered_paper.get_linked_papers_lists(
        add_uri=configuration.add_uri,
    )
    for k in ("recommendations", "rejections", "linked_by_refs"):
        r = lists.get(k)
        if r:
            return {k: r}
