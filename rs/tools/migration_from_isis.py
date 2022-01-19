import logging
import argparse
import json
import csv
import os
from datetime import datetime
from rs import (
    app,
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


def register_paper(json_file_path, log_file_path, journals, create_sources=False ,create_links=False):
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
    paper['create_sources'] = create_sources
    paper['create_links'] = create_links
    return app.receive_new_paper(**paper)


def register_papers(list_file_path, log_file_path, journals, create_sources, create_links):
    """
    """
    files_utils.write_file(log_file_path, "", "w")
    with open(list_file_path) as fp:
        for row in fp.readlines():
            registered = register_paper(row.strip(), log_file_path, journals,
                                        create_sources, create_links)
            if not registered:
                continue
            # registered['file_path'] = row.strip()
            # if registered.get("registered_paper"):
            #     registered['registered_paper'] = registered.get("registered_paper").pid
            # for k in ('recommended', 'rejected', 'selected_ids'):
            #     if registered.get(k):
            #         registered[k] = len(registered[k])
            registered['datetime'] = datetime.now().isoformat()
            content = json.dumps(registered)
            files_utils.write_file(log_file_path, content + "\n", "a")


def _split_list_in_n_lists(items, n=None):
    n = n or 4
    lists = []
    for i, item in enumerate(items):
        index = i % n
        try:
            lists[index].append(item)
        except IndexError:
            lists[index] = [item]
    print(f"Created {n} lists")
    print([len(l) for l in lists])
    return lists


def _get_article_json_file_path(folder_path, pid):
    return os.path.join(folder_path, pid[11:15], pid[1:10], pid)


def _get_article_json_file_paths(pid_csv_file_path, articles_json_folder_path):
    pids = [
        row['pid'] for row in files_utils.read_csv_file(pid_csv_file_path)
    ]
    return [
        _get_article_json_file_path(articles_json_folder_path, pid)
        for pid in sorted(pids, key=lambda pid: pid[11:15])
    ]


def _save_lists(lists, folder_path, filename_prefix, total):
    if not os.path.isdir(folder_path):
        os.makedirs(folder_path)

    # create the a list file for each call
    files_paths = []
    for i, list_rows in enumerate(lists):
        file_path = os.path.join(
            folder_path,
            f"{filename_prefix}_{i+1}_{len(list_rows)}_{total}.txt",
        )
        files_paths.append(file_path)
        files_utils.write_file(file_path, "\n".join(list_rows), "w")
    return files_paths


def _get_register_papers_command(
        articles_json_files_list_file_path,
        subject_areas_journals_csv_file_path,
        ):
    outputs_path = os.path.dirname(articles_json_files_list_file_path)
    basename = os.path.splitext(
        os.path.basename(articles_json_files_list_file_path))[0]

    output_jsonl_file_path = os.path.join(outputs_path, basename, ".jsonl")
    nohup_out_file_path = os.path.join(outputs_path, basename, ".out")

    # migration_from_isis must be registered as console_scripts entry_points in
    # setup.py
    return (
        "nohup migration_from_isis register_papers "
        f"{articles_json_files_list_file_path} {output_jsonl_file_path} "
        f"{subject_areas_journals_csv_file_path} "
        f" --create_sources --create_links>{nohup_out_file_path}&"
    )


def create_register_papers_sh(
        pid_csv_file_path, articles_json_folder_path,
        subject_areas_journals_csv_file_path,
        lists_folder_path, shell_script_path,
        list_filename_prefix=None,
        n_calls=None):

    json_file_paths = _get_article_json_file_paths(
        pid_csv_file_path, articles_json_folder_path,
    )
    lists = _split_list_in_n_lists(json_file_paths, n_calls or 4)
    prefix = (
        list_filename_prefix or
        os.path.splitext(os.path.basename(pid_csv_file_path))[0]
    )
    input_file_paths = _save_lists(
        lists, lists_folder_path, prefix, len(json_file_paths),
    )

    with open(shell_script_path, "w") as fp:
        for input_file_path in input_file_paths:
            command = _get_register_papers_command(
                input_file_path,
                subject_areas_journals_csv_file_path,
            )
            fp.write(f"{command}\n")
    return {
        "shell script": shell_script_path,
        "lists": input_file_paths,
    }


def main():
    parser = argparse.ArgumentParser(description="Migration tool")
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
    register_papers_parser.add_argument(
        "--create_sources",
        action=argparse.BooleanOptionalAction,
        default=False,
        help=(
            "/path/subject_areas.csv"
        )
    )
    register_papers_parser.add_argument(
        "--create_links",
        action=argparse.BooleanOptionalAction,
        default=False,
        help=(
            "/path/subject_areas.csv"
        )
    )

    create_register_papers_sh_parser = subparsers.add_parser(
        "create_register_papers_sh",
        help=(
            "Create shell script to call rs simultaneously"
        )
    )
    create_register_papers_sh_parser.add_argument(
        "pid_csv_file_path",
        help=(
            "/path/pid.csv"
        )
    )
    create_register_papers_sh_parser.add_argument(
        "articles_json_folder_path",
        help=(
            "Location of JSON files with article data: "
            "/path/articles_json_folder"
        )
    )
    create_register_papers_sh_parser.add_argument(
        "subject_areas_file_path",
        help=(
            "/path/subject_areas.csv"
        )
    )
    create_register_papers_sh_parser.add_argument(
        "lists_folder_path",
        help=(
            "/path/lists_folder"
        )
    )
    create_register_papers_sh_parser.add_argument(
        "shell_script_file_path",
        help=(
            "Shell script to run/path/run_rs.sh"
        )
    )
    create_register_papers_sh_parser.add_argument(
        "--list_filename_prefix",
        help=("Prefix for filename that contains the splitted list of pids")
    )
    create_register_papers_sh_parser.add_argument(
        "--simultaneous_calls",
        default=4,
        help=("Number of simultaneous call")
    )

    args = parser.parse_args()
    if args.command == "register_papers":
        journals = read_subject_areas(args.subject_areas_file_path)
        register_papers(
            args.list_file_path,
            args.log_file_path,
            journals,
            args.create_sources,
            args.create_links,
        )
    elif args.command == "register_paper":
        journals = read_subject_areas(args.subject_areas_file_path)
        register_paper(
            args.source_file_path,
            args.log_file_path,
            journals
        )
    elif args.command == "create_register_papers_sh":
        ret = create_register_papers_sh(
            args.pid_csv_file_path,
            args.articles_json_folder_path,
            args.subject_areas_file_path,
            args.lists_folder_path,
            args.shell_script_file_path,
            args.list_filename_prefix,
            args.simultaneous_calls,
        )
        print(ret)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
