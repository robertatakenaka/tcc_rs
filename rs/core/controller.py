import logging
from time import sleep

from rs.core import tasks, controller_
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
    paper.save()

    response = {}
    response.update(add_references_to_paper(paper, references))
    response["registered_paper"] = paper

    paper.save()

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
            print("not add reference")
            print(e)
            continue
        except Exception as e:
            print(e)
        else:
            if paper.recommendable == 'yes' and registered_ref.has_data_enough:
                print("call tasks.add_referenced_by_to_source")
                total_sources += 1
                tasks.add_referenced_by_to_source.apply_async((ref, paper._id))

    return {"total references": total, "total sources": total_sources}


def get_source_by_record_id(_id):
    return db.get_record_by__id(Source, _id)


def get_most_recent_paper_ids(paper_ids):
    items = []
    for _id in paper_ids:
        paper = get_paper_by_record_id(_id)
        items.append((paper.pub_year, _id))
    return [item[1] for item in sorted(items, reverse=True)]


def get_linked_papers_lists(pid):
    registered_paper = get_paper_by_pid(pid)
    lists = registered_paper.get_linked_papers_lists(
        add_uri=configuration.add_uri,
    )
    for k in ("recommendations", "rejections", "linked_by_refs"):
        r = lists.get(k)
        if r:
            return {k: r}


# def get_texts_papers_to_compare(selected_ids):
#     parameters = {}
#     if selected_ids:
#         # obtém os textos dos artigos
#         parameters['ids'], parameters['texts'] = (
#             get_texts_for_semantic_search(selected_ids)
#         )
#     print("get_texts_papers_to_compare", len(parameters))
#     return parameters
