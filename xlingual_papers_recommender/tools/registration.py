import argparse
import json
from copy import deepcopy

from xlingual_papers_recommender.core import (
    controller,
)
from xlingual_papers_recommender.utils import files_utils


def _create_papers_from_json_files(list_file_path, output_file_path):
    files_utils.write_file(output_file_path, "")
    with open(list_file_path) as fp:
        for json_file_path in fp.readlines():
            json_file_path = json_file_path.strip()
            response = _create_paper_from_json_file(json_file_path)
            files_utils.write_file(
                    output_file_path, json.dumps(response) + "\n", "a")


def _create_papers_from_json_files_split_abstracts(list_file_path, output_file_path):
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


def _create_paper_from_json_file(json_file_path):
    try:
        with open(json_file_path) as fp:
            data = fp.read()
        data = json.loads(data)
        response = controller.create_paper(**data)
    except Exception as e:
        response = {
            "json_file_path": json_file_path,
            "exception": str(type(e)), "msg": str(e),
        }
    return response


def create_papers_from_json_files(list_file_path, output_file_path, split_abstracts):
    if split_abstracts == "split_abstracts":
        _create_papers_from_json_files_split_abstracts(list_file_path, output_file_path)
    else:
        _create_papers_from_json_files(list_file_path, output_file_path)


def _display_response(response, pretty=True):
    if pretty:
        print(json.dumps(response, indent=2))
    else:
        print(response)


def main():
    parser = argparse.ArgumentParser(
        description="Crosslingual Papers Recommender Registration Tools")

    subparsers = parser.add_subparsers(
        title="Commands", metavar="", dest="command",
    )

    create_papers_from_json_files_parser = subparsers.add_parser(
        "create_papers_from_json_files",
        help=(
            "Register a list of papers"
        )
    )
    create_papers_from_json_files_parser.add_argument(
        "source_files_path",
        help=(
            "/path/documents.txt which contains a list of jsonl files"
        )
    )
    create_papers_from_json_files_parser.add_argument(
        "result_file_path",
        help=(
            "/path/result.jsonl"
        )
    )

    create_papers_from_json_files_parser.add_argument(
        "split_abstracts",
        help=(
            "split_abstracts"
        )
    )

    args = parser.parse_args()

    if args.command == "create_papers_from_json_files":
        create_papers_from_json_files(
            args.source_files_path, args.result_file_path, args.split_abstracts
        )

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
