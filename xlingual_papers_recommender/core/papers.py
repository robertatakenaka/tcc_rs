from xlingual_papers_recommender.db import (
    db,
)
from xlingual_papers_recommender import exceptions
from xlingual_papers_recommender import configuration
from xlingual_papers_recommender.db.data_models import (
    Paper,
    PROC_STATUS_NA,
    PROC_STATUS_SOURCE_REGISTERED,
    PROC_STATUS_TODO,
)
from xlingual_papers_recommender.utils import response_utils


REFERENCE_ATTRIBUTES = (
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
)


def create_paper():
    return Paper()


def get_paper_by_pid(pid):
    try:
        return db.get_records(Paper, **{'pid': pid})[0]
    except IndexError as e:
        raise exceptions.PaperNotFoundError(
            "Not found paper: %s %s" % (e, pid)
        )
    except Exception as e:
        raise exceptions.PaperNotFoundUnexpectedError(
            "Unexpected error: %s %s" % (e, pid)
        )


def get_paper_by_record_id(_id):
    try:
        return db.get_records(Paper, **{'_id': _id})[0]
    except IndexError as e:
        raise exceptions.PaperNotFoundError(
            "Not found paper: %s %s" % (e, _id)
        )
    except Exception as e:
        raise exceptions.PaperNotFoundUnexpectedError(
            "Unexpected error: %s %s" % (e, _id)
        )


def register_paper(network_collection, pid, main_lang, doi, pub_year,
                   uri,
                   subject_areas,
                   paper_titles,
                   abstracts,
                   keywords,
                   references,
                   extra=None,
                   ):
    response = response_utils.create_response("register_paper")
    try:
        paper = get_paper_by_pid(pid)
    except exceptions.PaperNotFoundError:
        paper = Paper()
    try:
        registered_paper = _register_paper(
            paper,
            network_collection, pid, main_lang, doi, pub_year,
            uri,
            subject_areas,
            paper_titles,
            abstracts,
            keywords,
            references,
            extra,
        )
        response['registered_paper'] = registered_paper._id
    except Exception as e:
        # mongoengine.errors.NotUniqueError
        # FIXME error code depende da excecao
        response_utils.add_error(response, "Unable to create paper", 400)
        response_utils.add_exception(response, e)
    return response


def _register_paper(paper, network_collection, pid, main_lang, doi, pub_year,
                    uri,
                    subject_areas,
                    paper_titles,
                    abstracts,
                    keywords,
                    references,
                    extra,
                    ):

    if configuration.ABSTRACTS_AND_REFERENCES_ARE_REQUIRED:
        if not abstracts or not references:
            raise exceptions.RequiredAbstractsAndReferencesError(
                "Paper registration requires abstracts and references"
            )
    main_lang = (
        main_lang or
        (paper_titles and paper_titles[0]['lang']) or
        (abstracts and abstracts[0]['lang'])
    )
    paper.clear()
    paper.extra = extra
    paper.network_collection = network_collection
    paper.pid = pid
    paper.pub_year = pub_year

    _add_uri(paper, uri, main_lang)
    paper.add_doi(main_lang, doi, 'UNK', 'UNK')

    if configuration.PAPERS_LOCATION_IS_REQUIRED:
        if not paper.uri and not paper.doi:
            raise exceptions.RequiredPaperDOIorPaperURIError(
                "Paper registration requires paper DOI or URI"
            )

    for subject_area in subject_areas:
        paper.add_subject_area(subject_area)

    paper.recommendable = 'no'
    for paper_title in paper_titles:
        try:
            paper.add_paper_title(paper_title['lang'], paper_title['text'])
            paper.recommendable = 'yes'
        except KeyError:
            pass

    for abstract in abstracts:
        try:
            paper.add_abstract(abstract['lang'], abstract['text'])
            paper.recommendable = 'yes'
        except KeyError:
            pass

    for keyword in keywords:
        try:
            paper.add_keyword(keyword['lang'], keyword['text'])
            paper.recommendable = 'yes'
        except KeyError:
            pass

    paper.save()

    for ref in references:
        _add_reference(paper, ref)

    if paper.proc_status != PROC_STATUS_SOURCE_REGISTERED:
        paper.proc_status = PROC_STATUS_NA
    paper.save()

    return paper


def _add_uri(paper, uri, main_lang):
    if isinstance(uri, str):
        paper.add_uri(main_lang, uri)
        return
    for item in uri:
        try:
            paper.add_uri(item.get("lang"), item['value'])
        except (KeyError, TypeError):
            raise exceptions.BadPaperURIFormatError(
                'Expected format for paper uri '
                '{"value": "uri value", "lang": "Language ISO Code 2-char"} ')


def _add_reference(paper, ref):
    for k in REFERENCE_ATTRIBUTES:
        ref[k] = ref.get(k) or None
    registered_ref = paper.add_reference(**ref)
    if paper.recommendable == 'yes' and registered_ref.has_data_enough:
        paper.proc_status = PROC_STATUS_SOURCE_REGISTERED
        print(PROC_STATUS_SOURCE_REGISTERED)


def get_parameters_to_get_ids_connected_by_references(paper_id):
    paper = get_paper_by_record_id(paper_id)
    if paper.proc_status == PROC_STATUS_TODO:
        from_year, to_year = configuration.get_years_range(paper)
        return {
            "paper_id": paper_id,
            "subject_areas": paper.subject_areas,
            "from_year": from_year,
            "to_year": to_year,
        }
    return None


def add_connection_by_semantic_similarity(paper_id, connected_paper_id, score):
    paper = get_paper_by_record_id(paper_id)
    paper.add_connection(connected_paper_id, score)
    paper.save()
