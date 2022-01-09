import os


MODELS_PATH = os.getenv('MODELS_PATH', default = "/path")


MODELS = [
    'stsb-xlm-r-multilingual',
    'chula-course-paraphrase-multilingual-mpnet-base-v2',
    'MSTSb_paraphrase-xlm-r-multilingual-v1',
    'distiluse-base-multilingual-cased-v2',
    'paraphrase-xlm-r-multilingual-v1',
    'paraphrase-multilingual-MiniLM-L12-v2',
    'paraphrase-multilingual-mpnet-base-v2',
]
DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', default = 'stsb-xlm-r-multilingual')


# mongodb://my_user:my_password@127.0.0.1:27017/my_db
DATABASE_CONNECT_URL = os.environ.get("DATABASE_CONNECT_URL")
MAX_CANDIDATES = int(os.environ.get("MAX_CANDIDATES") or 20)
MIN_SCORE = float(os.environ.get("MIN_SCORE") or 0.7)