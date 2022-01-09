class Document:

    def __init__(self):
        self.subject_area = None
        self.issn = None
        self.abstracts = None
        self.keywords = None
        self.article_titles = None
        self.references = None
        self.subject_area = None


def recommend_documents(document):
    # add subject area
    is_recommendable_doc = _is_recommendable_document(document)
    if not is_recommendable_doc:
        return
    document = _add_subject_area(document)
    recommendations = get_recommendations(document)
    register_recommendations(recommendations)
    return


def _is_recommendable_document(document):
    return any([
        document.abstracts,
        document.keywords,
        document.article_titles,
        document.references,
    ])


def _add_subject_area(document):
    document.subject_area = _get_subject_area(document.issn)
    if not document.subject_area:
        _predict_subject_area(document)
    return document


def _get_subject_area(issn):
    # TODO
    return "Health Sciences"


def _predict_subject_area(document):
    return "Health Sciences"


def get_recommendations(document):
    selected_documents = get_documents_selection(document)
    ranking = eval_similarity(document, selected_documents)
    return most_similar_documents(ranking)


def register_recommendations(recommendations):
    recommendations = []
    return recommendations


def get_documents_selection(document):
    return []


def eval_similarity(document, selection):
    return []


def most_similar_documents(ranking):
    return []
