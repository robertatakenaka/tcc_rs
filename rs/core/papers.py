from rs.db import (
    db,
)
from rs import exceptions
from rs import configuration
from rs.db.data_models import (
    Paper,
    PROC_STATUS_NA,
    PROC_STATUS_SOURCE_REGISTERED,
)
from rs.utils import response_utils


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


def get_paper_by_pid(pid):
    return db.get_records(Paper, **{'pid': pid})[0]


def get_paper_by_record_id(_id):
    return db.get_record_by__id(Paper, _id)


def create_paper(network_collection, pid, main_lang, doi, pub_year,
                 uri,
                 subject_areas,
                 paper_titles,
                 abstracts,
                 keywords,
                 references,
                 ):
    response = response_utils.create_response("create_paper")
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
        )
        response['registered_paper'] = registered_paper._id
    except Exception as e:
        # mongoengine.errors.NotUniqueError
        # FIXME error code depende da excecao
        response_utils.add_error(response, "Unable to create paper", 400)
        response_utils.add_exception(response, e)
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
    try:
        if configuration.RS_PAPER_ID_IS_REQUIRED_TO_UPDATE:
            if not _id:
                raise exceptions.MissingPaperIdError(
                    "Expected paper _id provided by Recommender System")

            registered_paper = get_paper_by_record_id(_id)
        else:
            if not pid:
                raise exceptions.MissingPaperIdError(
                    "Expected paper pid")
            registered_paper = get_paper_by_pid(pid)

        if not registered_paper:
            raise exceptions.UpdateDocumentError(
                "Document which _id=%s is not registered. " % _id)

        registered_paper = _register_paper(
            registered_paper,
            network_collection, pid, main_lang, doi, pub_year,
            uri,
            subject_areas,
            paper_titles,
            abstracts,
            keywords,
            references,
        )
        response['registered_paper'] = registered_paper._id
    except Exception as e:
        # FIXME error code depende da excecao
        response_utils.add_error(response, "Unable to update paper", 400)
        response_utils.add_exception(response, e)
    return response


def _register_paper(paper, network_collection, pid, main_lang, doi, pub_year,
                    uri,
                    subject_areas,
                    paper_titles,
                    abstracts,
                    keywords,
                    references,
                    ):

    if configuration.ABSTRACTS_AND_REFERENCES_ARE_REQUIRED:
        if not abstracts and not references:
            raise exceptions.RequiredAbstractsAndReferencesError(
                "Paper registration requires abstracts and references"
            )
    main_lang = (
        main_lang or
        (paper_titles and paper_titles[0]['lang']) or
        (abstracts and abstracts[0]['lang'])
    )
    paper.clear()
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
