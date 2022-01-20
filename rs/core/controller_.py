
from rs.utils import response_utils
from rs import exceptions
from rs.core import recommender
from rs.db import (
    db,
)
from rs.db.data_models import (
    Source,
    Paper,
    PROC_STATUS_TODO,
    PROC_STATUS_DONE,
)


def _db_connect(host):
    try:
        db.mk_connection(host)
    except:
        exit()


def search_sources(doi, pub_year, surname, organization_author, source,
                   journal, vol,
                   items_per_page, page, order_by):
    values = [doi, pub_year, surname, organization_author, source, journal, vol]
    if not any(values):
        raise exceptions.InsuficientArgumentsToSearchDocumentError(
            "rs.db.search_sources requires at least one argument: "
            "doi, pub_year, surname, organization_author, source, journal, vol"
        )
    field_names = [
        'doi', 'pub_year', 'surname', 'organization_author', 'source',
        'journal', 'vol',
    ]
    kwargs = db._get_kwargs(
        db._get_query_set_with_and(
            field_names, values), items_per_page, page, order_by
    )
    return db.get_records(Source, **kwargs)


def create_source(
        pub_year, vol, num, suppl, page, surname, organization_author, doi,
        journal, paper_title, source, issn,
        thesis_date, thesis_loc, thesis_country, thesis_degree, thesis_org,
        conf_date, conf_loc, conf_country, conf_name, conf_org,
        publisher_loc, publisher_country, publisher_name, edition,
        source_person_author_surname, source_organization_author,
        ):

    _source = Source()
    _source.pub_year = pub_year or None
    _source.vol = vol or None
    _source.num = num or None
    _source.suppl = suppl or None
    _source.page = page or None
    _source.surname = surname or None
    _source.organization_author = organization_author or None
    _source.doi = doi or None
    _source.journal = journal or None
    _source.paper_title = paper_title or None
    _source.source = source or None
    _source.issn = issn or None
    _source.thesis_date = thesis_date or None
    _source.thesis_loc = thesis_loc or None
    _source.thesis_country = thesis_country or None
    _source.thesis_degree = thesis_degree or None
    _source.thesis_org = thesis_org or None
    _source.conf_date = conf_date or None
    _source.conf_loc = conf_loc or None
    _source.conf_country = conf_country or None
    _source.conf_name = conf_name or None
    _source.conf_org = conf_org or None
    _source.publisher_loc = publisher_loc or None
    _source.publisher_country = publisher_country or None
    _source.publisher_name = publisher_name or None
    _source.edition = edition or None
    _source.source_person_author_surname = source_person_author_surname or None
    _source.source_organization_author = source_organization_author or None
    _source.save()
    return _source


def add_referenced_by_to_source(ref, paper_id, todo_mark, pid, year, subject_areas):
    try:
        page = 1
        items_per_page = 100
        order_by = None
        response = response_utils.create_response("add_referenced_by_to_source")
        sources = search_sources(
            ref['doi'], ref['pub_year'],
            ref['surname'], ref['organization_author'],
            ref['source'], ref['journal'], ref['vol'],
            items_per_page, page, order_by,
        )
    except exceptions.InsuficientArgumentsToSearchDocumentError as e:
        response_utils.add_exception(response, e)
        return response
    try:
        _source = sources[0]
    except (IndexError, TypeError, ValueError) as e:
        _source = create_source(**ref)
        _source.add_referenced_by(paper_id)
        _source.add_reflink(paper_id, pid, year, subject_areas)
        _source.save()
        response_utils.add_result(response, "source created")
        return response
    else:
        if paper_id not in _source.referenced_by:
            _source.add_referenced_by(paper_id)
            _source.add_reflink(paper_id, pid, year, subject_areas)
            _source.save()
            return todo_mark

        response_utils.add_result(
            response, "nothing to do: paper_id was registered in source")
        return response


def _get_linked_by_refs__papers_ids(paper_id):
    kwargs = {"referenced_by": paper_id}
    ids = set()
    for source in db.get_records(Source, **kwargs):
        ids.update(set(source.referenced_by))
        print(ids)
    if paper_id in ids:
        ids.remove(paper_id)
    return list(ids)


def _get_semantic_search_parameters(selected_ids, paper_id=None):
    parameters = {}
    if selected_ids:
        # obtém os textos dos artigos
        parameters['ids'], parameters['texts'] = (
            get_texts_for_semantic_search(selected_ids)
        )

        if paper_id:
            ign, text = (
                get_texts_for_semantic_search([paper_id])
            )
            parameters['text'] = text[0]
    print("get_semantic_search_parameters", len(parameters))
    return parameters


def get_text_for_semantic_search(paper):
    _text = []
    if not paper:
        return ""

    for items in (paper.paper_titles, paper.abstracts, paper.keywords):
        for item in items:
            _text.append(item.text)

    if _text:
        return "\n".join(_text)


def get_texts_for_semantic_search(paper_ids):
    selection = []
    valid_paper_ids = []
    for _id in paper_ids:
        print("get_texts_for_semantic_search", _id)
        text = get_text_for_semantic_search(get_paper_by_record_id(_id))
        if text:
            selection.append(text)
            valid_paper_ids.append(_id)
    print("valid selected_ids", len(valid_paper_ids))
    return valid_paper_ids, selection


def get_paper_by_record_id(_id):
    try:
        return db.get_record_by__id(Paper, _id)
    except Exception as e:
        print(e)
        print(_id)
        print("???????")


def _register_linked_papers(paper_id, recommended, rejected, ids):
    """
    Register links
    """
    registered_paper = get_paper_by_record_id(paper_id)
    registered_paper.recommendations = []
    registered_paper.rejections = []
    registered_paper.linked_by_refs = []

    for item in recommended:
        registered_paper.add_linked_paper(
            'recommendations', item['paper_id'], item['score'])
    for item in rejected:
        registered_paper.add_linked_paper(
            'rejections', item['paper_id'], item['score'])
    for item in ids:
        registered_paper.add_linked_paper(
            'linked_by_refs', item)
    registered_paper.proc_status = PROC_STATUS_DONE
    registered_paper.save()
    return registered_paper.get_linked_papers_lists()


def find_and_add_linked_papers_lists(paper_id):
    response = response_utils.create_response("find_and_add_linked_papers_lists")
    paper = get_paper_by_record_id(paper_id)
    if paper.proc_status != PROC_STATUS_TODO:
        response_utils.add_result(
            response, "Nothing done: PROC_STATUS=%s" % paper.proc_status)
        return response

    ids = _get_linked_by_refs__papers_ids(paper_id)
    if not ids:
        response_utils.add_result(response, "There is no `ids` to make links")
        return response

    parameters = _get_semantic_search_parameters(ids, paper_id)
    if not parameters:
        response_utils.add_result(
            response, "There is no `parameters` to make links")
        return response

    papers = recommender.compare_papers(**parameters)
    if not papers:
        response_utils.add_result(
            response, "Not found paper links")
        return response

    papers['ids'] = ids
    print(papers)
    result = _register_linked_papers(
        paper_id,
        papers.get('recommended'),
        papers.get('rejected'),
        papers.get('ids'),
    )
    return result

