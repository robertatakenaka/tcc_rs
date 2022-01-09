from rs.models.journal import get_subject_area
from rs.utils import pre_processing
from rs.core import recommender


def reception(document):
    # add subject area
    is_recommendable_doc = pre_processing.is_recommendable_document(document)
    if not is_recommendable_doc:
        return
    document = add_subject_area(document)
    return recommender.create_recommendations(document)


def add_subject_area(document):
    document.subject_area = get_subject_area(document.issn)
    if not document.subject_area:
        _predict_subject_area(document)
    return document


def _predict_subject_area(document):
    return "Health Sciences"

