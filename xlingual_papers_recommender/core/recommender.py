from xlingual_papers_recommender.core import (
    semantics,
)
from xlingual_papers_recommender import configuration


def compare_papers(text, ids, texts):
    """
    Atribui `score` de similaridade
    Parameters
    ----------
    text: str
        texto principal
    ids: str list
        ids dos papers para comparar
    texts: str list
        textos dos papers para comparar

    Returns
    -------
    list
        dict keys: paper_id, score
    """
    # se necessario
    # reduz a quantidade de candidatos para minimizar problemas de desempenho
    cut = []
    if len(ids) > configuration.MAX_CANDIDATES:
        cut = ids[:-configuration.MAX_CANDIDATES]
        ids = ids[-configuration.MAX_CANDIDATES:]
        texts = texts[-configuration.MAX_CANDIDATES:]
        # ids = controller.get_most_recent_paper_ids(ids)[:configuration.MAX_CANDIDATES]

    evaluated = semantics.compare_texts(text, ids, texts)
    return {"evaluated": evaluated, "cut": cut}
