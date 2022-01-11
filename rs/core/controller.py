import logging
from time import sleep

from rs.core import tasks
from rs import exceptions
from rs import configuration
from rs.db import (
    db,
)
from rs.db.data_models import (
    Paper,
    Source,
    Journal,
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

    response = {"registered_paper": paper}
    response.update(add_references_to_paper(paper, references))
    return response


def add_references_to_paper(paper, references):
    total = len(references)

    total_sources = 0
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
            LOGGER.info("not add reference")
            LOGGER.info(e)
            continue
        except Exception as e:
            LOGGER.info(e)
        else:
            if paper.recommendable == 'yes' and registered_ref.has_data_enough:
                LOGGER.info("call tasks.add_referenced_by_to_source")
                total_sources += 1
                tasks.add_referenced_by_to_source.apply_async((ref, paper._id))

    return {"total references": total, "total sources": total_sources}


def get_source_by_record_id(_id):
    return db.get_record_by__id(Source, _id)


def get_papers_ids_linked_by_references(registered_paper, total_sources=None):
    paper_id = registered_paper._id
    kwargs = {"referenced_by": paper_id}
    try:
        sources = db.get_records(Source, **kwargs)
        LOGGER.info("Found %i sources" % len(sources))
        if total_sources and not sources:
            sleep_s_time = (
                configuration.WAIT_SOURCES_REGISTRATIONS or total_sources
            )
            LOGGER.info("Sleep by %i" % sleep_s_time)
            LOGGER.info("total_sources=%i" % total_sources)
            sleep(sleep_s_time)
            sources = db.get_records(Source, **kwargs)
            LOGGER.info("total sources=%i" % len(sources))

        ids = set()
        for source in sources:
            ids.update(set(source.referenced_by))
        ids.remove(paper_id)
        return list(ids)
    except Exception as e:
        LOGGER.info(e)
        return []


def get_most_recent_paper_ids(paper_ids):
    items = []
    for _id in paper_ids:
        paper = get_paper_by_record_id(_id)
        items.append((paper.pub_year, _id))
    return [item[1] for item in sorted(items, reverse=True)]


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


def get_linked_papers_lists(pid):
    registered_paper = get_paper_by_pid(pid)
    lists = registered_paper.get_linked_papers_lists(
        add_uri=configuration.add_uri,
    )
    for k in ("recommendations", "rejections", "linked_by_refs"):
        r = lists.get(k)
        if r:
            return {k: r}

