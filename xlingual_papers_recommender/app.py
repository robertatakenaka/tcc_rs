import argparse
import json
from copy import deepcopy

from xlingual_papers_recommender.core import (
    controller,
)
from xlingual_papers_recommender.utils import files_utils
from xlingual_papers_recommender.configuration import DATABASE_CONNECT_URL


def register_papers(list_file_path, output_file_path, split_abstracts):
    """
    Registra `papers` a partir de um arquivo que contém uma lista de caminhos
    de arquivos JSON que contém dados de artigo
    """
    files_utils.write_file(output_file_path, "")
    for json_file_path in files_utils.read_file_rows(list_file_path):
        try:
            data = files_utils.read_file(json_file_path)
            data = json.loads(data)
            response = _register_papers(data, split_abstracts)
        except Exception as e:
            response = {
                "json_file_path": json_file_path,
                "exception": str(type(e)), "msg": str(e),
            }
        finally:
            files_utils.write_file(
                output_file_path, json.dumps(response) + "\n", "a")


def _register_papers(data, split_abstracts):
    if split_abstracts == "split_abstracts":
        responses = []
        for abstract in data['abstracts']:

            try:
                data_copy = deepcopy(data)
                pid = abstract.get("pid") or data_copy.get("pid")
                if not pid:
                    raise ValueError("PID is None for %s" % data)
                data_copy['abstracts'] = [abstract]
                data_copy['paper_titles'] = []
                data_copy['keywords'] = []
                data_copy['pid'] = pid + "_" + abstract['lang']
                data_copy['a_pid'] = pid

                response = register_paper(**data_copy)
            except Exception as e:
                response = {
                    "data": data,
                    "exception": str(type(e)), "msg": str(e),
                }
            finally:
                responses.append(response)
        return responses
    else:
        return register_paper(**data)


def register_paper(
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
    return controller.register_paper(
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
    parser = argparse.ArgumentParser(
        description="Main Papers Recommender System operations"
    )
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
        "--skip_update",
        type=bool,
        default=False,
        help=(
            "if it is already registered, skip_update do not update"
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
            "value for the minimum score. Ex.: 0.7"
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
    if not DATABASE_CONNECT_URL:
        raise ValueError("Invalid value for DATABASE_CONNECT_URL. Expected: mongodb://my_user:my_password@127.0.0.1:27017/my_db")

    if args.command == "receive_paper":
        paper_data = json.loads(files_utils.read_file(args.source_file_path))
        paper_data['skip_update'] = args.skip_update
        response = register_paper(**paper_data)
        files_utils.write_file(
            args.log_file_path, json.dumps(response) + "\n", "a")

    elif args.command == "register_new_papers":
        register_papers(
            args.source_files_path, args.result_file_path, args.split_abstracts
        )

    elif args.command == "search_papers":
        response = search_papers(
            args.text, args.subject_area, args.from_year, args.to_year)
        _display_response(response, pretty=False)

    elif args.command == "get_connected_papers":
        min_score = float(args.min_score or 0)
        response = get_connected_papers(args.pid, min_score)
        _display_response(response, pretty=False)

    elif args.command == "find_and_create_connections":
        response = find_and_create_connections(args.pid)
        _display_response(response, pretty=False)

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
