import os

from sentence_transformers import SentenceTransformer
from sentence_transformers.util import semantic_search

from xlingual_papers_recommender import configuration


_MODELS_PATH = configuration.MODELS_PATH
_DEFAULT_MODEL = configuration.DEFAULT_MODEL


def _get_model_path(model_name):
    path = os.path.join(_MODELS_PATH, model_name)
    if os.path.isdir(path):
        return path


def _get_sentence_transformer(model_name_or_path=None):
    model_name_or_path = (
        model_name_or_path or
        _get_model_path(model_name_or_path or _DEFAULT_MODEL) or
        _DEFAULT_MODEL
    )
    print("Usando %s" % model_name_or_path)
    return SentenceTransformer(model_name_or_path)


_SENTENCE_TRANSFORMER = _get_sentence_transformer()
print(_SENTENCE_TRANSFORMER)


def _gen_vectors(sentences, convert_to_tensor=True):
    print(">>> _gen_vectors")
    print(len(sentences))
    return _SENTENCE_TRANSFORMER.encode(
        sentences, convert_to_tensor=convert_to_tensor)


def _search(text, texts):
    print(">>> _search %s" % text)
    print(len(texts))

    # based on https://github.com/UKPLab/sentence-transformers/blob/master/examples/applications/semantic-search/semantic_search_publications.py
    query_embedding = _gen_vectors(text)

    corpus_embeddings = _gen_vectors(texts)

    print("Inicio semantic_search")
    search_hits = semantic_search(query_embedding, corpus_embeddings)
    print("Fim semantic_search")

    try:
        # Get the hits for the first query
        return search_hits[0]
    except IndexError:
        return


def compare_texts(text, ids, texts):
    ranking = []
    for found_item in _search(text, texts):
        index = found_item['corpus_id']
        ranking.append({'score': found_item['score'], 'paper_id': ids[index]})
    return ranking
