import os

##########################################

"""
https://www.sbert.net/docs/pretrained_models.html#multi-lingual-models

Semantic Similarity

These models find semantically similar sentences within one language or across languages:

    distiluse-base-multilingual-cased-v1: Multilingual knowledge distilled version of multilingual Universal Sentence Encoder. Supports 15 languages: Arabic, Chinese, Dutch, English, French, German, Italian, Korean, Polish, Portuguese, Russian, Spanish, Turkish.

    - distiluse-base-multilingual-cased-v2: Multilingual knowledge distilled version of multilingual Universal Sentence Encoder. This version supports 50+ languages, but performs a bit weaker than the v1 model.

    - paraphrase-multilingual-MiniLM-L12-v2 - Multilingual version of paraphrase-MiniLM-L12-v2, trained on parallel data for 50+ languages.

    - paraphrase-multilingual-mpnet-base-v2 - Multilingual version of paraphrase-mpnet-base-v2, trained on parallel data for 50+ languages.
"""

MODELS_PATH = os.getenv('MODELS_PATH', default="st_models")
MODELS = [
    'stsb-xlm-r-multilingual',
    'chula-course-paraphrase-multilingual-mpnet-base-v2',
    'MSTSb_paraphrase-xlm-r-multilingual-v1',
    'distiluse-base-multilingual-cased-v2',
    'paraphrase-xlm-r-multilingual-v1',
    'paraphrase-multilingual-MiniLM-L12-v2',
    'paraphrase-multilingual-mpnet-base-v2',
]
DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', default='paraphrase-xlm-r-multilingual-v1')
MAX_CANDIDATES = int(os.environ.get("MAX_CANDIDATES") or 20)
MIN_SCORE = float(os.environ.get("MIN_SCORE") or 0.7)

####################################################

# mongodb://my_user:my_password@127.0.0.1:27017/my_db
DATABASE_CONNECT_URL = os.environ.get("DATABASE_CONNECT_URL")
if not DATABASE_CONNECT_URL:
    raise ValueError("Not found value for DATABASE_CONNECT_URL")

WAIT_SOURCES_REGISTRATIONS = int(os.environ.get("WAIT_SOURCES_REGISTRATIONS") or 1)
ITEMS_PER_PAGE = int(os.environ.get("ITEMS_PER_PAGE") or 10)
RANGE_YEAR_DIFF = int(os.environ.get("RANGE_YEAR_DIFF") or 5)
####################################


CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", 'amqp://guest@0.0.0.0:5672//')
CELERY_RESULT_BACKEND_URL = os.environ.get("CELERY_RESULT_BACKEND_URL", 'rpc://')

PAPERS_REGISTRATION_QUEUE = os.environ.get("PAPERS_REGISTRATION_QUEUE", 'high_priority')
SOURCES_REGISTRATION_QUEUE = os.environ.get("SOURCES_REGISTRATION_QUEUE", 'default')
LINKS_REGISTRATION_QUEUE = os.environ.get("LINKS_REGISTRATION_QUEUE", 'low_priority')

PAPERS_GET_QUEUE = os.environ.get("PAPERS_GET_QUEUE", 'high_priority')
GET_IDS_CONNECTED_BY_REFERENCES_QUEUE = os.environ.get("GET_IDS_CONNECTED_BY_REFERENCES_QUEUE", 'high_priority')
GET_SEMANTIC_SEARCH_PARAMETERS_QUEUE = os.environ.get("GET_SEMANTIC_SEARCH_PARAMETERS_QUEUE", 'high_priority')
COMPARE_PAPERS_QUEUE = os.environ.get("COMPARE_PAPERS_QUEUE", 'high_priority')
REGISTER_PAPERS_CONNECTIONS_QUEUE = os.environ.get("REGISTER_PAPERS_CONNECTIONS_QUEUE", 'high_priority')
ADD_CONNECTION_QUEUE = os.environ.get("ADD_CONNECTION_QUEUE", 'low_priority')

REGISTER_ROW_QUEUE = os.environ.get("REGISTER_ROW_QUEUE", 'default')

####################################

COLLECTION_WEBSITE_URL_PATTERN = os.environ.get(
    "COLLECTION_WEBSITE_URL_PATTERN",
    default="{url}/documents/{id}"
)
PAPERS_LOCATION_IS_REQUIRED = bool(os.environ.get("PAPERS_LOCATION_IS_REQUIRED"))

RS_PAPER_ID_IS_REQUIRED_TO_UPDATE = bool(os.environ.get("RS_PAPER_ID_IS_REQUIRED_TO_UPDATE"))

# False = documentos serão registrados, no entanto, não serão recomendados
#             devido à ausência de referências
# True = somente serão registrados documentos que tem abstracts e references 
ABSTRACTS_AND_REFERENCES_ARE_REQUIRED = bool(os.environ.get("ABSTRACTS_AND_REFERENCES_ARE_REQUIRED") or True)


print(f"ABSTRACTS_AND_REFERENCES_ARE_REQUIRED={ABSTRACTS_AND_REFERENCES_ARE_REQUIRED}")

####################################


def get_paper_uri(url, paper_data):
    return COLLECTION_WEBSITE_URL_PATTERN.format(
            pid=paper_data['uri_params']['pid']
    )


def add_uri(paper_data):
    try:
        paper_data['uri'] = COLLECTION_WEBSITE_URL_PATTERN.format(
            url=paper_data['uri_params']['url'],
            id=paper_data['uri_params']['id'],

        )
    except KeyError:
        print(paper_data)
    return paper_data


def handle_text_s(paper_obj):
    words = set()
    for items in (paper_obj.paper_titles, paper_obj.abstracts, paper_obj.keywords):
        for item in items:
            words.update(set(_fix_text(item.text)))
    return " ".join(words)


def _fix_text(text):
    words = []
    for w in text.split():
        words.append("".join([c for c in w if c.isalnum()]).upper())
    return words


def get_years_range(paper_obj):
    # range could be set according to an "obsolence "index"
    return paper_obj.pub_year - RANGE_YEAR_DIFF, paper_obj.pub_year + RANGE_YEAR_DIFF
