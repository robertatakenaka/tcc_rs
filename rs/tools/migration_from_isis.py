import logging
import argparse
import json
import csv
import os

from rs.core import (
    reception,
)
from rs.utils import files_utils


expected_reference_attributes = (
    'pub_year', 'vol', 'num', 'suppl', 'page',
    'surname', 'organization_author', 'doi', 'journal',
    'paper_title', 'source', 'issn', 'thesis_date',
    'thesis_loc', 'thesis_country', 'thesis_degree', 'thesis_org',
    'conf_date', 'conf_loc', 'conf_country', 'conf_name', 'conf_org',
    'publisher_loc', 'publisher_country', 'publisher_name', 'edition',
    'source_person_author_surname', 'source_organization_author',
)


def fix_csv_ref_attributes(reference_from_csv_file):
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
        value = reference_from_csv_file.get(k) or ''
        ref[k] = value.split("^")[0]

    ref['pub_year'] = (reference_from_csv_file.get("pub_date") or '')[:4]
    ref['organization_author'] = (reference_from_csv_file.get("corpauth") or '').split("^")[0]
    ref['source_organization_author'] = (reference_from_csv_file.get("source_corpauth") or '').split("^")[0]
    ref['source_person_author_surname'] = (reference_from_csv_file.get("source_author") or '').split("^")[0]
    ref['paper_title'] = (reference_from_csv_file.get("article_title") or '').split("^")[0]
    ref['source'] = (ref['source'] or '').split("^")[0]
    ref['paper_title'] = (ref['paper_title'] or '').split("^")[0]
    return ref


def convert_paper(data, journals):
    original_paper = data['articles'][0]

    paper_titles = []
    for item in data.get("article_titles") or []:
        paper_titles.append({"lang": item["lang"], "text": item["text"]})

    abstracts = []
    for item in data.get("abstracts") or []:
        abstracts.append({"lang": item["lang"], "text": item["text"]})

    keywords = []
    for item in data.get("keywords") or []:
        keywords.append({"lang": item["lang"], "text": item["text"]})

    references = []
    for ref in (data.get("references") or data.get("references_long_pids_parcial") or []):
        references.append(fix_csv_ref_attributes(ref))

    subject_areas = original_paper.get("subject_areas") or []
    if not subject_areas:
        j = journals.get(original_paper['pid'][1:10])
        if j:
            subject_areas = j

    return dict(
        network_collection=original_paper['collection'],
        pid=original_paper['pid'],
        main_lang=data['articles_langs'][0]['value'],
        doi=original_paper['doi'],
        pub_year=original_paper['pub_date'][:4],
        subject_areas=subject_areas,
        paper_titles=paper_titles,
        abstracts=abstracts,
        keywords=keywords,
        references=references,
    )


def read_subject_areas(file_path):
    journals = {}

    with open(file_path) as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            issn = row['key']
            journals[issn] = journals.get(issn) or []
            journals[issn].append(row['value'])

    return journals


def register_paper(json_file_path, log_file_path, journals):
    """
    """
    print(json_file_path)
    content = files_utils.read_file(json_file_path)
    try:
        data = json.loads(content)
    except Exception as e:
        print(e)
        logging.exception("Unable to read %s" % json_file_path)
        return
    if not data.get("references"):
        ref_file_path = json_file_path + "_refs.json"
        if os.path.isfile(ref_file_path):
            refs = json.loads(files_utils.read_file(ref_file_path))
            data.update(refs)
    try:
        paper = convert_paper(data, journals)
    except KeyError:
        return
    return reception.receive_paper(paper)


def register_papers(list_file_path, log_file_path, journals):
    """
    """
    with open(list_file_path) as fp:
        for row in fp.readlines():
            registered = register_paper(row.strip(), log_file_path, journals)
            if not registered:
                continue
            registered['file_path'] = row.strip()
            if registered.get("registered_paper"):
                registered['registered_paper'] = registered.get("registered_paper").pid
            for k in ('recommended', 'rejected', 'selected_ids'):
                if registered.get(k):
                    registered[k] = len(registered[k])
            content = json.dumps(registered)
            files_utils.write_file(log_file_path, content + "\n", "a")


def main():
    parser = argparse.ArgumentParser(description="Network pid manager tool")
    subparsers = parser.add_subparsers(title="Commands", metavar="", dest="command")

    register_paper_parser = subparsers.add_parser(
        "register_paper",
        help=(
            "Register a paper from document.json file. "
        )
    )
    register_paper_parser.add_argument(
        "source_file_path",
        help=(
            "/path/document.json"
        )
    )
    register_paper_parser.add_argument(
        "log_file_path",
        help=(
            "/path/registered.jsonl"
        )
    )
    register_paper_parser.add_argument(
        "subject_areas_file_path",
        help=(
            "/path/subject_areas.csv"
        )
    )

    register_papers_parser = subparsers.add_parser(
        "register_papers",
        help=(
            "Register documents from a list of document.json file paths"
        )
    )
    register_papers_parser.add_argument(
        "list_file_path",
        help=(
            "/path/list.txt"
        )
    )
    register_papers_parser.add_argument(
        "log_file_path",
        help=(
            "/path/registered.jsonl"
        )
    )
    register_papers_parser.add_argument(
        "subject_areas_file_path",
        help=(
            "/path/subject_areas.csv"
        )
    )

    args = parser.parse_args()
    if args.command == "register_papers":
        journals = read_subject_areas(args.subject_areas_file_path)
        register_papers(args.list_file_path, args.log_file_path, journals)
    elif args.command == "register_paper":
        journals = read_subject_areas(args.subject_areas_file_path)
        register_paper(
            args.source_file_path,
            args.log_file_path,
            journals
        )
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
