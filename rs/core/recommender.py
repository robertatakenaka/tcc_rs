from rs.core import (
    semantics,
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
