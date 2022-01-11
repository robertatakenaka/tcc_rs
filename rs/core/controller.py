import logging

from rs import exceptions
from rs.db import (
    db,
)
from rs.db.data_models import (
    Paper,
    Source,
    Journal,
)


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
                 ):
    paper = Paper()
    return _update_paper(
        paper,
        network_collection, pid, main_lang, doi, pub_year,
        subject_areas,
        paper_titles,
        abstracts,
        keywords,
        references,
    )


def update_paper(paper, network_collection, pid, main_lang, doi, pub_year,
                 subject_areas,
                 paper_titles,
                 abstracts,
                 keywords,
                 references,
                 ):
    return _update_paper(
        paper,
        network_collection, pid, main_lang, doi, pub_year,
        subject_areas,
        paper_titles,
        abstracts,
        keywords,
        references,
    )


def _update_paper(paper, network_collection, pid, main_lang, doi, pub_year,
                  subject_areas,
                  paper_titles,
                  abstracts,
                  keywords,
                  references,
                  ):
    main_lang = (
        main_lang or
        (paper_titles and paper_titles[0]['lang']) or
        (abstracts and abstracts[0]['lang'])
    )
    paper.clear()
    paper.network_collection = network_collection
    paper.pid = pid
    paper.pub_year = pub_year

    paper.add_doi(main_lang, doi, 'UNK', 'UNK')

    for subject_area in subject_areas:
        paper.add_subject_area(subject_area)

    recommendable = None
    for paper_title in paper_titles:
        recommendable = 'yes'
        try:
            paper.add_paper_title(paper_title['lang'], paper_title['text'])
        except KeyError:
            pass

    for abstract in abstracts:
        recommendable = 'yes'
        try:
            paper.add_abstract(abstract['lang'], abstract['text'])
        except KeyError:
            pass

    for keyword in keywords:
        try:
            paper.add_keyword(keyword['lang'], keyword['text'])
        except KeyError:
            pass

    paper.recommendable = recommendable or 'no'
    paper = paper.save()

    add_references_to_paper(paper, references)

    return paper.save()


def add_references_to_paper(paper, references):
    total = len(references)

    for ref in references:
        for k in (
                "pub_year",
                "vol",
                "num",
                "suppl",
                "page",
                "surname",
                "organization_author",
                "doi",
                "journal",
                "paper_title",
                "source",
                "issn",
                "thesis_date",
                "thesis_loc",
                "thesis_country",
                "thesis_degree",
                "thesis_org",
                "conf_date",
                "conf_loc",
                "conf_country",
                "conf_name",
                "conf_org",
                "publisher_loc",
                "publisher_country",
                "publisher_name",
                "edition",
                "source_person_author_surname",
                "source_organization_author",
            ):
            ref[k] = ref.get(k) or None
        try:
            registered_ref = paper.add_reference(**ref)
        except TypeError as e:
            print("not add reference")
            print(e)
            continue
        except Exception as e:
            print(e)

        if paper.recommendable == 'yes' and registered_ref.has_data_enough:
            _add_referenced_by_to_source(ref, paper._id)

    added = len(paper.references)
    logging.debug("added %i/%i references to paper %s" % (added, total, paper.id))


def _add_referenced_by_to_source(ref, paper_id):
    try:
        page = 1
        items_per_page = 100
        order_by = None
        sources = search_sources(
            ref['doi'], ref['pub_year'], ref['surname'], ref['organization_author'],
            ref['source'], ref['journal'], ref['vol'],
            items_per_page, page, order_by,
        )
    except exceptions.InsuficientArgumentsToSearchDocumentError as e:
        print("InsuficientArgumentsToSearchDocumentError")
        print(e)
        return
    try:
        _source = sources[0]
    except (IndexError, TypeError, ValueError) as e:
        _source = create_source(**ref)
    
    try:
        _source.add_referenced_by(paper_id)
        _source.save()
    except Exception as e:
        print("source not saved")
        print(e)


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
    return _source


def get_source_by_record_id(_id):
    return db.get_record_by__id(Source, _id)


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
        db._get_query_set_with_and(field_names, values), items_per_page, page, order_by
    )
    return db.get_records(Source, **kwargs)


def get_papers_ids_linked_by_references(registered_paper):
    paper_id = str(registered_paper.id)
    kwargs = {"referenced_by": paper_id}
    sources = db.get_records(Source, **kwargs)
    try:
        ids = set()
        for source in sources:
            ids.update(set(source.referenced_by))
        ids.remove(paper_id)
        return list(ids)
    except:
        return []


def get_most_recent_paper_ids(paper_ids):
    items = []
    for _id in paper_ids:
        paper = get_paper_by_record_id(_id)
        items.append((paper.pub_year, _id))
    return [item[1] for item in sorted(items, reverse=True)]


def get_papers(paper_ids):
    selection = []
    for _id in paper_ids:
        selection.append(get_paper_by_record_id(_id))
    return selection


def get_text_for_semantic_search(paper):
    _text = []
    if not paper:
        return ""
    if paper.paper_titles:
        _text.append(paper.paper_titles[0].text)

    if paper.abstracts:
        _text.append(paper.abstracts[0].text)

    if _text:
        return "\n".join(_text)


def get_texts_for_semantic_search(paper_ids):
    selection = []
    valid_paper_ids = []
    for _id in paper_ids:
        text = get_text_for_semantic_search(get_paper_by_record_id(_id))
        if text:
            selection.append(text)
            valid_paper_ids.append(_id)
    return valid_paper_ids, selection


def register_recommendations(registered_paper, recommendations):
    if not recommendations:
        return
    for recommendation in recommendations:
        recommended = get_paper_by_record_id(recommendation['paper_id'])
        registered_paper.add_recommendation(
            recommended.pid, recommended.network_collection,
            recommended.pub_year, recommended.doi_with_lang,
            recommended.paper_titles, recommended.abstracts,
            recommendation['score'],
        )
    response = []
    for item in registered_paper.recommendations:
        response.append(item.as_dict())
    return response


def register_rejections(registered_paper, rejections):
    if not rejections:
        return
    for rejection in rejections:
        rejected = get_paper_by_record_id(rejection['paper_id'])
        registered_paper.add_rejection(
            rejected.pid, rejected.network_collection,
            rejected.pub_year, rejected.doi_with_lang,
            rejected.paper_titles, rejected.abstracts,
            rejection['score'],
        )
    response = []
    for item in registered_paper.rejections:
        response.append(item.as_dict())
    return response


def register_linked_by_refs(registered_paper, related_papers_ids):
    if not related_papers_ids:
        return
    for _id in related_papers_ids:
        related = get_paper_by_record_id(_id)
        if not related:
            continue
        registered_paper.add_linked_by_refs(
            related.pid, related.network_collection,
            related.pub_year, related.doi_with_lang,
            related.paper_titles, related.abstracts,
        )
    response = []
    for item in registered_paper.linked_by_refs:
        response.append(item.as_dict())
    return response


def register_paper_links(registered_paper, recommended, rejected, linked_by_refs):
    """
    Register links
    """
    # registra os resultados na base de dados
    response = {}
    if recommended:
        response['recommendations'] = (
            register_recommendations(registered_paper, recommended)
        )
    if rejected:
        response['rejections'] = (
            register_rejections(registered_paper, rejected)
        )
    if linked_by_refs:
        response['linked_by_refs'] = (
            register_linked_by_refs(registered_paper, linked_by_refs)
        )
    registered_paper.save()
    return response


def get_paper_links(pid):
    data = {}
    registered_paper = get_paper_by_pid(pid)
    data['registered_paper'] = registered_paper.as_dict()
    data.update(registered_paper.links)
    return data
