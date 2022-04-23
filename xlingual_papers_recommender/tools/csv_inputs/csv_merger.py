from copy import deepcopy


expected_reference_attributes = (
    'pub_year', 'vol', 'num', 'suppl', 'page',
    'surname', 'organization_author', 'doi', 'journal',
    'paper_title', 'source', 'issn', 'thesis_date',
    'thesis_loc', 'thesis_country', 'thesis_degree', 'thesis_org',
    'conf_date', 'conf_loc', 'conf_country', 'conf_name', 'conf_org',
    'publisher_loc', 'publisher_country', 'publisher_name', 'edition',
    'source_person_author_surname', 'source_organization_author',
)


def merge_data(pid, records):
    data = dict(
        network_collection=None,
        pid=pid,
        main_lang=None,
        doi=None,
        pub_year=None,
        uri='',
        subject_areas=None,
        paper_titles=None,
        abstracts=None,
        keywords=None,
        references=None,
    )

    for record in records:
        record_data = record["data"]

        data["network_collection"] = (
            data.get("network_collection") or record_data.get("collection") or record_data.get("collection.x")
        )
        data["main_lang"] = (
            data.get("main_lang") or record_data.get("lang")
        )
        data["doi"] = (
            data.get("doi") or record_data.get("doi")
        )
        data["pub_year"] = (
            data.get("pub_year") or pid[10:14]
        )

        if record_data.get("subject_areas"):
            data = add_item(
                data, "subject_areas", record_data["subject_areas"])

        if record["name"] in ("paper_titles", "abstracts", "keywords"):
            item = dict(
                text=record_data.get("original"),
                lang=record_data["lang"],
            )
            data = add_item(data, record_data["name"], item)
        elif record["name"] == "references":
            item = fix_csv_ref_attributes(record_data)
            data = add_item(data, record_data["name"], item)
    return data


def add_item(data, data_label, item):
    data[data_label] = data.get(data_label) or []
    if item not in data[data_label]:
        data[data_label].append(item)
    return data


def fix_csv_ref_attributes(csv_row):
    """
    {"surname": "Paterson",
    "conf_org": "",
    "vol": "34",
    "conf_name": "",
    "pid": "S0011-8516202100010001000003",
    "source_author": "",
    "thesis_org": "",
    "num": "52",
    "thesis_degree": "",
    "publisher_country": "",
    "publisher_name": "",
    "article_title": "Vaccine hesitancy and healthcare providers",
    "suppl": "",
    "source": "",
    "thesis_date": "",
    "publisher_loc": "",
    "journal": "Vaccine",
    "thesis_loc": "",
    "collection": "sza",
    "corpauth": "",
    "conf_loc": "",
    "pub_date": "20160000",
    "thesis_country": "",
    "doi": "",
    "edition": "",
    "issn": "0264-410X",
    "conf_date": "",
    "conf_country": "",
    "page": "6700-6",
    "source_corpauth": ""}
    """
    ref = {}
    for k in expected_reference_attributes:
        value = (csv_row.get(k) or '').strip()
        ref[k] = value.split("^")[0]

    ref['pub_year'] = (csv_row.get("pub_date") or '')[:4]
    ref['organization_author'] = (csv_row.get("corpauth") or '').split("^")[0]
    ref['source_organization_author'] = (csv_row.get("source_corpauth") or '').split("^")[0]
    ref['source_person_author_surname'] = (csv_row.get("source_author") or '').split("^")[0]
    ref['paper_title'] = (csv_row.get("article_title") or '').split("^")[0] or None
    ref['source'] = (ref['source'] or '').split("^")[0]
    return ref


# def read_subject_areas(file_path):
#     journals = {}

#     with open(file_path) as fp:
#         reader = csv.DictReader(fp)
#         for row in reader:
#             issn = row['key']
#             journals[issn] = journals.get(issn) or set()
#             journals[issn].add(row['value'])

#     return journals


def split_one_paper_into_n_papers(pid, paper_data):
    items = []
    for abstract in paper_data.get("abstracts") or []:
        try:
            data_copy = deepcopy(paper_data)
            data_copy['abstracts'] = [abstract]
            data_copy['pid'] = pid + "_" + abstract['lang']
            data_copy['main_lang'] = abstract['lang']
            data_copy['a_pid'] = pid
            items.append(data_copy)
        except Exception:
            continue
    return items

