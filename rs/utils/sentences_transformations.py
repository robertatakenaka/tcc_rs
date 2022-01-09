from random import choice

from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim
import numpy as np


def _gen_vectors(sentences, model_name):
    model = SentenceTransformer(model_name)
    return model.encode(sentences)


def _compare_vectors(vector, vectors):
    return cos_sim(vector, vectors)


def try_models(words):
    _models = [
        'distiluse-base-multilingual-cased-v1',
        'distiluse-base-multilingual-cased-v2',
        'paraphrase-multilingual-MiniLM-L12-v2',
        'paraphrase-multilingual-mpnet-base-v2',
    ]
    for m in _models:
        print("")
        print(m)
        print(words)
        for i in range(len(words)-1):
            _word = words[i]
            _words = words[i+1:]
            find_similars(_word, _words, m)


def find_similars(word, words, model):
    vector = _gen_vectors([word], model)
    vectors = _gen_vectors(words, model)
    result = _compare_vectors(vector, vectors)
    r = result.tolist()

    for i in range(len(words)):
        highlight = "*"*3 if r[0][i] > 0.9 else ""
        print(f"{word}\t{words[i]}\t{r[0][i]}\t{highlight}")
