import os

##########################################
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
DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', default='stsb-xlm-r-multilingual')
MAX_CANDIDATES = int(os.environ.get("MAX_CANDIDATES") or 20)
MIN_SCORE = float(os.environ.get("MIN_SCORE") or 0.7)

####################################################

# mongodb://my_user:my_password@127.0.0.1:27017/my_db
DATABASE_CONNECT_URL = os.environ.get("DATABASE_CONNECT_URL")
if not DATABASE_CONNECT_URL:
    raise ValueError("Not found value for DATABASE_CONNECT_URL")

WAIT_SOURCES_REGISTRATIONS = int(os.environ.get("WAIT_SOURCES_REGISTRATIONS") or 1)
ITEMS_PER_PAGE = int(os.environ.get("ITEMS_PER_PAGE") or 10)

####################################

CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", 'amqp://guest@0.0.0.0:5672//')
CELERY_RESULT_BACKEND_URL = os.environ.get("CELERY_RESULT_BACKEND_URL", 'rpc://')

####################################

COLLECTION_WEBSITE_URL_PATTERN = os.environ.get(
    "COLLECTION_WEBSITE_URL_PATTERN",
    default="{url}/documents/{id}"
)

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
    for items in (paper_obj.keywords, paper_obj.paper_titles, paper_obj.abstracts):
        for item in items:
            words.union(set(item.text.split()))
    return " ".join(words)
