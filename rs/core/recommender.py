from rs.core import (
    semantics,
    controller,
)
from rs import configuration


def compare_papers(text, ids, texts):
    """
    Identifica os papers mais e menos similares

    Parameters
    ----------
    text: str
        texto principal
    ids: str list
        ids dos papers para comparar
    texts: str lisg
        textos dos papers para comparar

    Returns
    -------
    dict
        keys: recommended, rejected

    """
    # se necessario
    # reduz a quantidade de candidatos para minimizar problemas de desempenho
    if len(ids) > configuration.MAX_CANDIDATES:
        ids = ids[-configuration.MAX_CANDIDATES:]
        texts = texts[-configuration.MAX_CANDIDATES:]
        # ids = controller.get_most_recent_paper_ids(ids)[:configuration.MAX_CANDIDATES]

    items = semantics.compare_texts(text, ids, texts)
    response = {}
    response['recommended'] = []
    response['rejected'] = []
    for item in items:
        if item['score'] > float(configuration.MIN_SCORE):
            response['recommended'].append(item)
        else:
            response['rejected'].append(item)
    return response


def find_links_for_registered_paper(registered_paper, selected_ids):
    if not registered_paper:
        return {
            "msg": "Unable to get links for register paper: "
                   "missing registered_paper parameter"}

    if not selected_ids:
        return {
            "msg": "Unable to get links for register paper: "
                   "missing selected_ids parameter"}

    text = controller.get_text_for_semantic_search(registered_paper)
    return find_paper_links(text, selected_ids)


def find_paper_links(text, selected_ids):
    if not text:
        return {
            "msg": "Unable to discover paper links: "
                   "missing text parameter"}
    if not selected_ids:
        return {
            "msg": "Unable to discover paper links: "
                   "missing selected_ids parameter"}

    parameters = {}
    parameters['text'] = text

    # obtém os textos dos artigos
    parameters['ids'], parameters['texts'] = (
        controller.get_texts_for_semantic_search(selected_ids)
    )
    try:
        papers = compare_papers(**parameters)
    except TypeError:
        papers = {}

    papers['selected_ids'] = selected_ids
    return papers
