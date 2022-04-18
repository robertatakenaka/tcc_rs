from html import unescape

from xlingual_papers_recommender.db import (
    db,
)
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
        return db.get_records(CSVRow, **{'pid': pid})
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
        lang = row["lang"]
    except KeyError as e:
        raise csv_inputs_exceptions.RequiredInputDataNotFoundError(
            "Required pid, lang, name: %s %s" % (e, row)
        )
    return pid, lang, name


def register_row(row):
    """
    Register "csv_row"
    """
    response = response_utils.create_response("create_row")
    try:
        row = _fix_row(row)
        pid, lang, name = _get_fields(row)

        try:
            csv_row = _get_csv_row(pid, lang, name)
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

def merge_csv(pid):
    """
    Register paper data as JSON
    """
    response = response_utils.create_response("merge_csv")
    try:
        response['merged'] = _merge_csv(pid)
    except (
            csv_inputs_exceptions.CSVRowNotFoundError,
            csv_inputs_exceptions.CSVRowNotFoundUnexpectedError,
            Exception,
            ) as e:
        response_utils.add_error(response, "Unable to register paper data as JSON", 400)
        response_utils.add_exception(response, e)
    return response


def _merge_csv(pid):
    """
    Merge cvs_row records, creating a JSON
    """
    records = _get_cvs_row_records(pid)
    return csv_merger.merge_data(pid, records)


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
    paper_json.save()
    return paper_json


def get_registered_paper_json(pid):
    try:
        return db.get_records(PaperJSON, **{'pid': pid})[0]
    except IndexError as e:
        raise csv_inputs_exceptions.PaperJsonNotFoundError(
            "Not found cvs_row: %s %s" % (e, pid)
        )
    except Exception as e:
        raise csv_inputs_exceptions.PaperJsonNotFoundUnexpectedError(
            "Unexpected error: %s %s" % (e, pid)
        )
