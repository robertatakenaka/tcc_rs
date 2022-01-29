from datetime import datetime
from rs.configuration import (
    ITEMS_PER_PAGE, add_uri, get_years_range
)
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


# def _db_connect(host):
#     try:
#         db.mk_connection(host)
#     except:
#         exit()


def search_sources(doi, pub_year, surname, organization_author, source,
                   journal, vol,
                   items_per_page, page, order_by):
    if doi:
        records = search_sources_by_doi(doi)
        try:
            source = records[0]
        except IndexError:
            pass
        else:
            return records
    return search_sources_by_data(
        doi, pub_year, surname, organization_author, source,
        journal, vol,
        items_per_page, page, order_by
    )


def search_sources_by_doi(doi):
    if not doi:
        raise exceptions.SourceSearchInputError(
            "rs.db.search_sources_by_doi requires doi"
        )
    kwargs = {'doi': doi}
    return db.get_records(Source, **kwargs)


def search_sources_by_data(doi, pub_year, surname, organization_author, source,
                           journal, vol,
                           items_per_page, page, order_by):
    try:
        pub_year = int(pub_year)
        if len(str(pub_year)) != 4:
            raise ValueError("pub_year has not 4 digits")
        max_value = datetime.now().year + 1
        if pub_year > max_value:
            raise ValueError("pub_year must be <= %i" % max_value)
    except (TypeError, ValueError) as e:
        raise exceptions.SourceSearchInputError(
            "Error: %s. Value of `pub_year`=%s. It must be a number with 4 digits. " % (e, pub_year)
        )

    values = [doi, pub_year, surname, organization_author, source, journal, vol]
    if not any(values):
        raise exceptions.SourceSearchInputError(
            "rs.db.search_sources requires at least one argument: "
            "doi, pub_year, surname, organization_author, source, journal, vol"
        )
    values.extend([items_per_page, page, order_by])
    field_names = (
        'doi', 'pub_year', 'surname', 'organization_author', 'source',
        'journal', 'vol', 'items_per_page', 'page', 'order_by',
    )

    kwargs = {
        k: v
        for k, v in zip(field_names, values)
        if v
    }
    return db.get_records(Source, **kwargs)


def create_source(
        pub_year, vol, num, suppl, page, surname, organization_author, doi,
        journal, paper_title, source, issn,
        thesis_date, thesis_loc, thesis_country, thesis_degree, thesis_org,
        conf_date, conf_loc, conf_country, conf_name, conf_org,
        publisher_loc, publisher_country, publisher_name, edition,
        source_person_author_surname, source_organization_author,
        ):

    if not doi:
        try:
            pub_year = int(pub_year)
            if len(str(pub_year)) != 4:
                raise ValueError("pub_year has not 4 digits")
            max_value = datetime.now().year + 1
            if pub_year > max_value:
                raise ValueError("pub_year must be <= %i" % max_value)
        except (TypeError, ValueError) as e:
            raise exceptions.SourceCreationInputError(
                "Error: %s. Value of `pub_year`=%s. It must be a number with 4 digits. " % (e, pub_year)
            )

    _source = Source()
    _source.pub_year = pub_year
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


def _get_ids_connected_by_references(paper_id, subject_areas=None, from_year=None, to_year=None):
    if not paper_id:
        raise exceptions.ReferenceConnectionSearchInputError(
            "_get_ids_connected_by_references requires paper_id parameter"
        )
    params = dict(
        referenced_by=paper_id,
        reflinks__subject_areas__in=subject_areas,
        reflinks__year__gte=int(from_year or 0),
        reflinks__year__lte=int(to_year or 0),
    )
    kwargs = {
        k: v
        for k, v in params.items()
        if v
    }
    reflinks = set()
    print(kwargs)
    for source in db.get_records(Source, **kwargs):
        print(source._id)
        t = source.get_reflinks_tuples()
        print(t)
        reflinks.update(set(t))

    reflinks = sorted(reflinks)
    print(len(reflinks))
    if any([subject_areas, from_year, to_year]):
        print([subject_areas, from_year, to_year])
        return list(
            _filter_results(
                reflinks, paper_id, subject_areas, from_year, to_year
            )
        )
    return [
        item
        for item in reflinks
        if item[-1] != paper_id
    ]


def _filter_results(reflinks, paper_id, subject_areas, from_year, to_year):
    for item in reflinks:
        if _valid_reflink(item, paper_id, subject_areas, from_year, to_year):
            yield item[-1]


def _valid_reflink(item, paper_id, subject_areas, from_year, to_year):
    reflink_year, reflink_subject_areas, ign, reflink_paper_id = item

    if paper_id == reflink_paper_id:
        # it is itself, skip
        return False

    if subject_areas and not (set(subject_areas) & set(reflink_subject_areas)):
        return False

    if from_year and to_year:
        return from_year <= reflink_year <= to_year
    if from_year and (from_year <= reflink_year):
        return True
    if to_year:
        return reflink_year <= to_year
    return False


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


def _register_papers_connections(paper_id, evaluated, ids):
    """
    Register links
    """
    registered_paper = get_paper_by_record_id(paper_id)
    registered_paper.connections = []
    for item in evaluated:
        registered_paper.add_connection(item['paper_id'], item['score'])
    for item in ids:
        registered_paper.add_connection(item)

    if evaluated:
        registered_paper.proc_status = PROC_STATUS_DONE

    registered_paper.save()
    return registered_paper.get_connections()


def find_and_create_connections(paper_id):
    response = response_utils.create_response("find_and_create_connections")
    paper = get_paper_by_record_id(paper_id)
    if paper.proc_status != PROC_STATUS_TODO:
        response_utils.add_result(
            response, "Nothing done: PROC_STATUS=%s" % paper.proc_status)
        return response

    years_range = get_years_range(paper)
    ids = _get_ids_connected_by_references(
        paper_id, paper.subject_areas, *years_range)
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
        response_utils.add_result(response, "Not found paper links")
        return response

    result = _register_papers_connections(
        paper_id,
        papers['evaluated'],
        papers['cut'],
    )
    return result


##############################################################################

def search_papers(text, subject_areas, from_year, to_year):
    selected_ids = _select_papers_ids_by_text(
        text, subject_areas, from_year, to_year)
    parameters = _get_semantic_search_parameters(selected_ids)

    papers = recommender.compare_papers(
        text, parameters['ids'], parameters['texts']
    )
    items = []
    for item in papers['evaluated']:
        paper = get_paper_by_record_id(item['paper_id'])
        paper_data = add_uri(paper.as_dict())
        paper_data['score'] = item['score']
        items.append(paper_data)

    response = {
        "text": text,
        "recommendations": items,
    }
    return response


def _select_papers_ids_by_text(
        text, subject_areas=None, from_year=None, to_year=None,
        page=None, items_per_page=None, order_by=None,
        ):
    page = page or 1
    items_per_page = items_per_page or ITEMS_PER_PAGE
    order_by = order_by or '-pub_year'

    # FIXME
    words = set(text.split())
    selected_ids = set()
    for word in words:
        _ids = _select_papers_ids_by_word(
            word, subject_areas,
            from_year, to_year,
            items_per_page, page, order_by,
        )
        selected_ids |= set(_ids)
    return list(selected_ids)


def _select_papers_ids_by_word(
        text, subject_areas,
        from_year, to_year,
        page=None, items_per_page=None, order_by=None,
        ):
    page = page or 1
    items_per_page = items_per_page or ITEMS_PER_PAGE
    order_by = order_by or '-pub_year'

    registered_papers = _search_papers(
        text, subject_areas,
        from_year, to_year,
        items_per_page, page, order_by,
    )
    ids = set()
    for paper in registered_papers:
        ids |= set(_get_ids_connected_by_references(
                        paper._id, subject_areas,
                        from_year, to_year))
        ids |= set([paper._id])

    return ids


def _search_papers(text, subject_areas,
                   begin_year, end_year,
                   items_per_page, page, order_by,
                   ):
    if not text:
        raise exceptions.InsuficientArgumentsToSearchDocumentError(
            "searcher._search_papers requires text parameter"
        )
    values = [subject_areas, begin_year, end_year, ]
    field_names = [
        'subject_areas__in',
        'pub_year__gte',
        'pub_year__lte',
    ]
    kwargs = {
        k: v
        for k, v in zip(field_names, values)
        if v
    }
    return Paper.objects(**kwargs).search_text(text).order_by('$text_score')
