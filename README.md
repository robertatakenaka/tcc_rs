
# What is it?

Component of a papers recommender system in a cross-lingual and multidisciplinary scope.

Result of the Coursework of MBA in Data Science and Analytics - USP / ESALQ - 2020-2022.

Designed to be customizable in many ways:

- sentence-transformer model
- the maximum number of candidate articles for the evaluation of semantic similarity
- accepts any type of document that has bibliographic references


# Dependences

- sentence-transformer
- celery
- mongoengine


# Model

The algorithm adopted is a combination of recommender systems graph based and content based filtering with semantic similarity

The identification of the relationship between scientific articles is made during the document's entry into the system through the common bibliographic references. Subsequently, the documents are ranked by semantic similarity and recorded in a database.

The recommendation system works in two steps: creating links between articles via common citations and assigning a similarity coefficient for a selection of these linked articles. 

The system itself does not establish which articles should be recommended. 

The recommendation system client defines which articles to present as a recommendation depending on the criticality of the use case.


# Installation

```console
pip install -U xlingual_papers_recommender
```

# Configurations

```console
export DATABASE_CONNECT_URL=mongodb://my_user:my_password@127.0.0.1:27017/my_db
export CELERY_BROKER_URL="amqp://guest@0.0.0.0:5672//"
export CELERY_RESULT_BACKEND_URL="rpc://"
export MODELS_PATH=sentence_transformers_models
export DEFAULT_MODEL=paraphrase-xlm-r-multilingual-v1

```

# Celery

## Start service

```console
celery -A xlingual_papers_recommender.core.tasks worker -l info -Q default,low_priority,high_priority --pool=solo --autoscale 8,4 --loglevel=DEBUG
```

## Clean queue

```console
celery worker -Q low_priority,default,high_priority --purge
```

# Usage

## Register new paper

```console
xlingual_papers_recommender receive_paper [--skip_update SKIP_UPDATE] source_file_path log_file_path
```

positional arguments:
  source_file_path      /path/document.json
  log_file_path         /path/registered.jsonl

optional arguments:
  -h, --help            show this help message and exit
  --skip_update SKIP_UPDATE
                        if it is already registered, skip_update do not update


Examples of source_file_path:

```
docs
└── examples
    ├── document1.json
    ├── document2.json
    ├── document3.json
    ├── document4.json
    ├── document5.json
    ├── document51.json
    ├── document6.json
    ├── document6_2.json
    ├── document7.json
    └── document7_2.json
```

References attributes:

- pub_year
- vol
- num
- suppl
- page
- surname
- organization_author
- doi
- journal
- paper_title
- source
- issn
- thesis_date
- thesis_loc
- thesis_country
- thesis_degree
- thesis_org
- conf_date
- conf_loc
- conf_country
- conf_name
- conf_org
- publisher_loc
- publisher_country
- publisher_name
- edition
- source_person_author_surname
- source_organization_author


## Get paper recommendations

```console
usage: xlingual_papers_recommender get_connected_papers [-h] [--min_score MIN_SCORE] pid

positional arguments:
  pid                   pid

optional arguments:
  -h, --help            show this help message and exit
  --min_score MIN_SCORE
                        min_score
```


## Load papers data from datasets


### Register parts

```console
usage: xlingual_papers_recommender_ds_loader register_paper_part [-h] [--skip_update SKIP_UPDATE] [--pids_selection_file_path PIDS_SELECTION_FILE_PATH]
                                                                 {abstracts,references,keywords,paper_titles,articles} input_csv_file_path output_file_path

positional arguments:
  {abstracts,references,keywords,paper_titles,articles}
                        part_name
  input_csv_file_path   CSV file with papers part data
  output_file_path      jsonl output file path

optional arguments:
  -h, --help            show this help message and exit
  --skip_update SKIP_UPDATE
                        True to skip if paper is already registered
  --pids_selection_file_path PIDS_SELECTION_FILE_PATH
                        Selected papers ID file path (CSV file path which has "pid" column)
```


#### Register articles

Example:

```console
xlingual_papers_recommender_ds_loader register_paper_part articles articles.csv articles.jsonl
```

** Required columns**

- pid
- main_lang
- uri
- subject_areas
- pub_year
- doi (optional)
- network_collection (optional)


#### Register abstracts

Example:

```console
xlingual_papers_recommender_ds_loader register_paper_part abstracts /inputs/abstracts.csv /outputs/abstracts.jsonl
```

**Columns**

- pid
- lang
- original
- text (padronizado)

Same for `paper_titles` and `keywords` datasets.


#### Register references

Example:

```console
xlingual_papers_recommender_ds_loader register_paper_part references /inputs/references.csv /outputs/references.jsonl
```

**Columns**

- pub_year
- vol
- num
- suppl
- page
- surname
- organization_author
- doi
- journal
- paper_title
- source
- issn
- thesis_date
- thesis_loc
- thesis_country
- thesis_degree
- thesis_org
- conf_date
- conf_loc
- conf_country
- conf_name
- conf_org
- publisher_loc
- publisher_country
- publisher_name
- edition
- source_person_author_surname
- source_organization_author


## Merge papers parts

```
usage: xlingual_papers_recommender_ds_loader merge_parts [-h] [--split_into_n_papers SPLIT_INTO_N_PAPERS] [--create_paper CREATE_PAPER]
                                                         input_csv_file_path output_file_path

positional arguments:
  input_csv_file_path   Selected papers ID file path (CSV file path which has "pid" column)
  output_file_path      jsonl output file path

optional arguments:
  -h, --help            show this help message and exit
  --split_into_n_papers SPLIT_INTO_N_PAPERS
                        True to create one register for each abstract
  --create_paper CREATE_PAPER
                        True to register papers
```

Example:

```console
xlingual_papers_recommender_ds_loader merge_parts pids.csv output.jsonl
```

## Register papers from loaded datasets

```
usage: xlingual_papers_recommender_ds_loader register_paper [-h] [--skip_update SKIP_UPDATE] input_csv_file_path output_file_path

positional arguments:
  input_csv_file_path   Selected papers ID file path (CSV file path which has "pid" column)
  output_file_path      jsonl output file path

optional arguments:
  -h, --help            show this help message and exit
  --skip_update SKIP_UPDATE
                        True to skip if paper is already registered
```

Example:

```console
xlingual_papers_recommender_ds_loader register_paper pids.csv output.jsonl
```


## Generate reports from papers, sources and connections

```
usage: xlingual_papers_recommender_reports all [-h] reports_path

positional arguments:
  reports_path  /path

optional arguments:
  -h, --help    show this help message and exit
```

Example:

```console
xlingual_papers_recommender_reports all /reports
```

