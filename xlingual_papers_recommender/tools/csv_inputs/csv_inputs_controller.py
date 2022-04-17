from xlingual_papers_recommender.db import (
    db,
)
from xlingual_papers_recommender import configuration
from xlingual_papers_recommender.tools.csv_inputs.csv_inputs_models import CSVRow
from xlingual_papers_recommender.tools.csv_inputs import csv_inputs_exceptions

from xlingual_papers_recommender.utils import response_utils


def get_record_by_pid(pid, lang, name):
    try:
        return db.get_records(
            CSVRow, **{'pid': pid, 'lang': lang, 'name': name})[0]
    except IndexError:
        raise csv_inputs_exceptions.CSVRowNotFoundError(
            "%s %s %s %s" % (e, pid, lang, name)
        )
    except Exception as e:
        raise csv_inputs_exceptions.CSVRowNotFoundUnexpectedError(
            "%s %s %s %s" % (e, pid, lang, name)
        )


def get_fields(row):
    try:
        pid = row["pid"]
        lang = row["lang"]
        name = row["name"]
    except KeyError:
        raise csv_inputs_exceptions.RequiredInputDataNotFoundError(
            "Required pid, lang, name: %s %s" % (e, row)
        )
    return pid, lang, name


def register_row(row):
    response = response_utils.create_response("create_row")
    try:
        pid, lang, name = get_fields(row)

        try:
            csv_row = get_record_by_pid(pid, lang, name)
        except csv_inputs_exceptions.CSVRowNotFoundError:
            csv_row = CSVRow()
        registered_row = _register_row(csv_row, pid, lang, name, row)
        response['registered_row'] = registered_row._id
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
