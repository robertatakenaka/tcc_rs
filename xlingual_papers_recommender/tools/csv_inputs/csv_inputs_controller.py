from html import unescape

from xlingual_papers_recommender.db import (
    db,
)
from xlingual_papers_recommender.core import controller
from xlingual_papers_recommender.utils import response_utils
from xlingual_papers_recommender.tools.csv_inputs.csv_inputs_models import (
    CSVRow,
    PaperJSON,
)
from xlingual_papers_recommender.tools.csv_inputs import (
    csv_inputs_exceptions,
    csv_merger,
)


def _get_cvs_row_records(pid):
    try:
        return db.get_records(CSVRow, **{'pid': pid, 'items_per_page': 500})
    except IndexError as e:
        raise csv_inputs_exceptions.CSVRowNotFoundError(
            "Not found cvs_row: %s %s" % (e, pid)
        )
    except Exception as e:
        raise csv_inputs_exceptions.CSVRowNotFoundUnexpectedError(
            "Unexpected error: %s %s" % (e, pid)
        )


def _get_csv_row(pid, lang, name):
    try:
        return db.get_records(
            CSVRow, **{'pid': pid, 'lang': lang, 'name': name})[0]
    except IndexError as e:
        raise csv_inputs_exceptions.CSVRowNotFoundError(
            "Not found cvs_row: %s %s %s %s" % (e, pid, lang, name)
        )
    except Exception as e:
        raise csv_inputs_exceptions.CSVRowNotFoundUnexpectedError(
            "Unexpected error: %s %s %s %s" % (e, pid, lang, name)
        )


def _fix_row(row):
    if len(row["pid"]) == 28:
        row["ref_pid"] = row["pid"]
        row["pid"] = row["pid"][:23]
        row["lang"] = ''
    for k, v in row.items():
        try:
            row[k] = unescape(v)
        except:
            pass
    return row


def _get_fields(row):
    try:
        pid = row["pid"]
        name = row["name"]
        lang = row.get("lang") or row.get("ref_pid")
    except KeyError as e:
        raise csv_inputs_exceptions.RequiredInputDataNotFoundError(
            "Required pid, lang, name: %s %s" % (e, row)
        )
    return pid, lang, name


def register_row(row, skip_update):
    """
    Register "csv_row"
    """
    response = response_utils.create_response("create_row")
    try:
        row = _fix_row(row)
        pid, lang, name = _get_fields(row)

        response['params'] = {'pid': pid, 'skip_update': skip_update}

        try:
            csv_row = _get_csv_row(pid, lang, name)
            if skip_update:
                # item is already registered then skip update
                return response
        except csv_inputs_exceptions.CSVRowNotFoundError:
            csv_row = CSVRow()
        registered = _register_row(csv_row, pid, lang, name, row)
        response['registered'] = registered.as_dict()
    except Exception as e:
        # mongoengine.errors.NotUniqueError
        # FIXME error code depende da excecao
        response_utils.add_error(response, "Unable to create row", 400)
        response_utils.add_exception(response, e)
    return response


def _register_row(csv_row, pid, lang, name, row):
    csv_row.pid = pid
    csv_row.lang = lang
    csv_row.name = name
    csv_row.data = row
    csv_row.save()
    return csv_row


####################################

def merge_csv(pid, split):
    """
    Register paper data as JSON
    """
    response = response_utils.create_response("merge_csv")
    try:
        # obtém os registros das partes de um artigo
        records = _get_cvs_row_records(pid)

        print("records: ")
        print(len(records))

        # une os dados das partes do artigo
        paper = csv_merger.merge_data(pid, records)
        print("merged abstracts")
        print(paper['abstracts'])

        if split:
            # gera N artigos a partir de um artigo com N resumos
            papers = csv_merger.split_one_paper_into_n_papers(pid, paper)
        else:
            papers = [paper]
        response['papers'] = papers
    except (
            csv_inputs_exceptions.CSVRowNotFoundError,
            csv_inputs_exceptions.CSVRowNotFoundUnexpectedError,
            Exception,
            ) as e:
        response_utils.add_error(response, "Unable to get paper json", 400)
        response_utils.add_exception(response, e)
    return response


def register_paper_data_as_json(input_data):
    """
    Register paper data as JSON
    """
    response = response_utils.create_response("register_paper_data_as_json")
    try:
        pid = input_data["pid"]
        try:
            paper_json = get_registered_paper_json(pid)
        except csv_inputs_exceptions.PaperJsonNotFoundError:
            paper_json = PaperJSON()
        registered = _register_paper_data_as_json(
            paper_json, pid, input_data)
        response['registered'] = registered.as_dict()
    except Exception as e:
        # mongoengine.errors.NotUniqueError
        # FIXME error code depende da excecao
        response_utils.add_error(response, "Unable to register paper data as JSON", 400)
        response_utils.add_exception(response, e)
    return response


def _register_paper_data_as_json(paper_json, pid, input_data):
    paper_json.pid = pid
    paper_json.data = input_data
    paper_json.a_pid = input_data.get("a_pid") or input_data.get("pid")
    paper_json.save()
    return paper_json


def get_registered_paper_json(pid):
    try:
        return db.get_records(PaperJSON, **{'a_pid': pid})[0]
    except IndexError as e:
        raise csv_inputs_exceptions.PaperJsonNotFoundError(
            "Not found paper_json: %s %s" % (e, pid)
        )
    except Exception as e:
        raise csv_inputs_exceptions.PaperJsonNotFoundUnexpectedError(
            "Unexpected error: %s %s" % (e, pid)
        )


def json_to_paper(pid, skip_update=None):
    responses = []
    print(pid)
    json_papers = db.get_records(PaperJSON, **{'a_pid': pid})
    print(len(json_papers))
    for j_paper in json_papers:
        print(j_paper.data["pid"], j_paper.data["a_pid"])
        resp = {}
        paper_data = j_paper.data
        paper_data = _fix_args_to_create_paper(paper_data)
        paper_data['skip_update'] = skip_update
        resp.update(paper_data)

        _resp = controller.register_paper(**paper_data)
        resp.update(_resp)

        responses.append(resp)
    return responses


def _fix_args_to_create_paper(data):
    return dict(
        network_collection=data.get('collection'),
        pid=data['pid'],
        main_lang=data.get("main_lang") or data.get("lang") or '',
        doi=data.get("doi"),
        pub_year=data['pid'][10:14],
        uri=data.get("uri") or '',
        subject_areas=list(set(data.get("subject_areas") or [])),
        paper_titles=data.get("paper_titles") or [],
        abstracts=data.get("abstracts") or [],
        keywords=data.get("keywords") or [],
        references=data.get("references") or [],
        extra=data.get("extra"),
    )
