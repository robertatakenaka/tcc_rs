import argparse
import json
from copy import deepcopy

from xlingual_papers_recommender.core import (
    controller,
)
from xlingual_papers_recommender.utils import files_utils


def _register_new_papers(list_file_path, output_file_path):
    files_utils.write_file(output_file_path, "")
    with open(list_file_path) as fp:
        for json_file_path in fp.readlines():
            json_file_path = json_file_path.strip()
            try:
                with open(json_file_path) as fpj:
                    data = fpj.read()
                data = json.loads(data)
                response = controller.create_paper(**data)
            except Exception as e:
                response = {
                    "json_file_path": json_file_path,
                    "exception": str(type(e)), "msg": str(e),
                }
            finally:
                files_utils.write_file(
                    output_file_path, json.dumps(response) + "\n", "a")


def _register_new_papers_split_abstracts(list_file_path, output_file_path):
    files_utils.write_file(output_file_path, "")
    with open(list_file_path) as fp:
        for json_file_path in fp.readlines():
            json_file_path = json_file_path.strip()
            try:
                with open(json_file_path) as fpj:
                    data = fpj.read()
                data = json.loads(data)
                for abstract in data['abstracts']:

                    try:
                        data_copy = deepcopy(data)
                        pid = abstract.get("pid") or data_copy.get("pid")
                        if not pid:
                            raise ValueError("PID is None for %s" % json_file_path)
                        data_copy['abstracts'] = [abstract]
                        data_copy['paper_titles'] = []
                        data_copy['keywords'] = []
                        data_copy['pid'] = pid + "_" + abstract['lang']
                        response = controller.create_paper(**data_copy)
                    except Exception as e:
                        response = {
                            "json_file_path": json_file_path,
                            "exception": str(type(e)), "msg": str(e),
                        }
                    finally:
                        files_utils.write_file(
                            output_file_path, json.dumps(response) + "\n", "a")

            except Exception as e:
                response = {
                    "json_file_path": json_file_path,
                    "exception": str(type(e)), "msg": str(e),
                }
            finally:
                files_utils.write_file(
                    output_file_path, json.dumps(response) + "\n", "a")


def register_new_papers(list_file_path, output_file_path, split_abstracts):
    if split_abstracts == "split_abstracts":
        _register_new_papers_split_abstracts(list_file_path, output_file_path)
    else:
        _register_new_papers(list_file_path, output_file_path)


def receive_new_paper(
        network_collection, pid, main_lang, doi, pub_year,
        uri,
        subject_areas,
        paper_titles,
        abstracts,
        keywords,
        references, extra=None,
        ):
    """
    Cria paper
    """
    return controller.create_paper(
        network_collection, pid, main_lang, doi, pub_year,
        uri,
        subject_areas,
        paper_titles,
        abstracts,
        keywords,
        references, extra,
    )


def update_paper(
        _id,
        network_collection, pid, main_lang, doi, pub_year,
        uri,
        subject_areas,
        paper_titles,
        abstracts,
        keywords,
        references, extra=None,
        ):
    """
    Atualiza paper
    """
    return controller.update_paper(
        _id,
        network_collection, pid, main_lang, doi, pub_year,
        uri,
        subject_areas,
        paper_titles,
        abstracts,
        keywords,
        references, extra,
    )


def search_papers(text, subject_area, from_year, to_year):
    return controller.search_papers(text, subject_area, from_year, to_year)


def get_connected_papers(pid, min_score=None):
    return controller.get_connected_papers(pid, min_score)


def find_and_create_connections(pid):
    return controller.find_and_create_connections(pid)


def _display_response(response, pretty=True):
    if pretty:
        print(json.dumps(response, indent=2))
    else:
        print(response)


def main():
    parser = argparse.ArgumentParser(description="Recommender System utils")
    subparsers = parser.add_subparsers(
        title="Commands", metavar="", dest="command",
    )

    receive_paper_parser = subparsers.add_parser(
        "receive_paper",
        help=(
            "Create or update a paper"
        )
    )
    receive_paper_parser.add_argument(
        "action",
        help=(
            "new or update"
        )
    )
    receive_paper_parser.add_argument(
        "source_file_path",
        help=(
            "/path/document.json"
        )
    )
    receive_paper_parser.add_argument(
        "log_file_path",
        help=(
            "/path/registered.jsonl"
        )
    )

    register_new_papers_parser = subparsers.add_parser(
        "register_new_papers",
        help=(
            "Register a list of papers"
        )
    )
    register_new_papers_parser.add_argument(
        "source_files_path",
        help=(
            "/path/documents.txt"
        )
    )
    register_new_papers_parser.add_argument(
        "result_file_path",
        help=(
            "/path/result.jsonl"
        )
    )

    register_new_papers_parser.add_argument(
        "split_abstracts",
        help=(
            "split_abstracts"
        )
    )

    search_papers_parser = subparsers.add_parser(
        "search_papers",
        help=(
            "Search papers"
        )
    )
    search_papers_parser.add_argument(
        "text",
        help=(
            "text"
        )
    )
    search_papers_parser.add_argument(
        "--subject_area",
        help=(
            "subject_area"
        )
    )
    search_papers_parser.add_argument(
        "--from_year",
        help=(
            "from_year"
        )
    )
    search_papers_parser.add_argument(
        "--to_year",
        help=(
            "to_year"
        )
    )

    get_connected_papers_parser = subparsers.add_parser(
        "get_connected_papers",
        help=(
            "Get paper links"
        )
    )
    get_connected_papers_parser.add_argument(
        "pid",
        help=(
            "pid"
        )
    )
    get_connected_papers_parser.add_argument(
        "--min_score",
        help=(
            "min_score"
        )
    )

    find_and_create_connections_parser = subparsers.add_parser(
        "find_and_create_connections",
        help=(
            "Update linked papers lists"
        )
    )
    find_and_create_connections_parser.add_argument(
        "pid",
        help=(
            "pid"
        )
    )

    args = parser.parse_args()
    if args.command == "receive_paper":
        paper_data = json.loads(files_utils.read_file(args.source_file_path))
        if args.action == "new":
            response = receive_new_paper(**paper_data)
        else:
            response = update_paper(**paper_data)
        files_utils.write_file(
            args.log_file_path, json.dumps(response) + "\n", "a")

    elif args.command == "register_new_papers":
        register_new_papers(
            args.source_files_path, args.result_file_path, args.split_abstracts
        )

    elif args.command == "search_papers":
        response = search_papers(
            args.text, args.subject_area, args.from_year, args.to_year)
        _display_response(response, pretty=False)

    elif args.command == "get_connected_papers":
        response = get_connected_papers(args.pid, args.min_score)
        _display_response(response, pretty=False)

    elif args.command == "find_and_create_connections":
        response = find_and_create_connections(args.pid)
        _display_response(response, pretty=False)

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
