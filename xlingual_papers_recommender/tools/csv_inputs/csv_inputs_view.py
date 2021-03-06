import logging
import argparse
import json
import os
from datetime import datetime

from xlingual_papers_recommender.core import tasks
from xlingual_papers_recommender.utils import files_utils
from xlingual_papers_recommender.tools.csv_inputs import csv_inputs_controller


def write_output_file(output_file_path, response):
    with open(output_file_path, "a") as fp:
        try:
            s = json.dumps(response)
            fp.write(f"{s}\n")
        except Exception as e:
            print(e)
            print(response)


def register_paper_part(part_name, input_csv_file_path, output_file_path, skip_update, pids_selection_file_path):
    """
    Lê um arquivo CSV que contém um dos dados de artigo, por exemplo:
    references, langs, abstracts, ... e insere este dado no arquivo JSON
    do artigo correspondente
    """
    try:
        inclusion_list = [
            item["pid"]
            for item in files_utils.read_csv_file(pids_selection_file_path)
        ]
    except:
        inclusion_list = []

    with open(output_file_path, "w") as fp:
        fp.write("")

    for row in files_utils.read_csv_file(input_csv_file_path):

        if pids_selection_file_path and not inclusion_list:
            break

        try:
            if len(row["pid"]) == 28:
                row["ref_pid"] = row["pid"]
                row["pid"] = row["pid"][:23]
                row["lang"] = row["ref_pid"]
            row['name'] = part_name

            if row['pid'] in inclusion_list:
                inclusion_list.remove(row['pid'])
                response = tasks.register_csv_row_data(row, skip_update)
            elif not pids_selection_file_path:
                response = tasks.register_csv_row_data(row, skip_update)
            else:
                response = {"pid": row['pid'], "skip_ingress": True}

        except KeyError as e:
            response = {"error": "Missing pid %s" % str(row)}
        except ValueError as e:
            response = row
        except Exception as e:
            response = {"error": "Ingress csv. Unexpected error %s %s" % (str(row), e)}

        write_output_file(output_file_path, response)


def csv_rows_to_json(input_csv_file_path, output_file_path, split=False):
    """
    Lê um arquivo CSV que contém um dos dados de artigo, por exemplo:
    references, langs, abstracts, ... e insere este dado no arquivo JSON
    do artigo correspondente
    """
    with open(output_file_path, "w") as fp:
        fp.write("")

    for row in files_utils.read_csv_file(input_csv_file_path):
        try:
            print(row)
            pid = row["pid"]
            response = tasks.csv_rows_to_json(pid, split)
        except KeyError as e:
            response = {"error": "Missing pid %s" % str(row)}
        except ValueError as e:
            response = row
        except Exception as e:
            response = {"error": "Create json from csv. Unexpected error %s %s" % (str(row), e)}

        write_output_file(output_file_path, response)


def json_to_paper(input_csv_file_path, output_file_path, skip_update):
    """
    Lê um arquivo CSV que contém um dos dados de artigo, por exemplo:
    references, langs, abstracts, ... e insere este dado no arquivo JSON
    do artigo correspondente
    """

    with open(output_file_path, "w") as fp:
        fp.write("")

    for row in files_utils.read_csv_file(input_csv_file_path):
        print(row)
        try:
            pid = row["pid"]
            response = csv_inputs_controller.json_to_paper(pid, skip_update)
        except KeyError as e:
            response = {"error": "Missing pid %s" % str(row)}
        except ValueError as e:
            response = {"error": "%s %s" % (row, str(e))}
        except Exception as e:
            response = {"error": "Register paper. Unexpected error %s %s" % (str(row), e)}

        write_output_file(output_file_path, response)


def main():
    parser = argparse.ArgumentParser(description="Input tools")
    subparsers = parser.add_subparsers(title="Commands", metavar="", dest="command")

    register_paper_part_parser = subparsers.add_parser(
        'register_paper_part',
        help=("Load papers data from CSV file (abstracts, references, keywords, paper_titles, articles)")
    )
    register_paper_part_parser.add_argument(
        'part_name',
        choices=["abstracts", "references", "keywords", "paper_titles", "articles"],
        help='part_name'
    )
    register_paper_part_parser.add_argument(
        'input_csv_file_path',
        help='CSV file with papers part data'
    )
    register_paper_part_parser.add_argument(
        'output_file_path',
        help='jsonl output file path'
    )
    register_paper_part_parser.add_argument(
        '--skip_update',
        type=bool,
        default=False,
        help='True to skip if paper is already registered'
    )
    register_paper_part_parser.add_argument(
        '--pids_selection_file_path',
        default=None,
        help='Selected papers ID file path (CSV file path which has "pid" column)'
    )

    merge_parts_parser = subparsers.add_parser(
        'merge_parts',
        help=("Merge papers parts")
    )
    merge_parts_parser.add_argument(
        'input_csv_file_path',
        help='Selected papers ID file path (CSV file path which has "pid" column)'
    )
    merge_parts_parser.add_argument(
        'output_file_path',
        help='jsonl output file path'
    )
    merge_parts_parser.add_argument(
        '--split_into_n_papers',
        default=None,
        help='True to create one register for each abstract'
    )
    merge_parts_parser.add_argument(
        '--create_paper',
        type=bool,
        default=False,
        help='True to register papers'
    )

    register_paper_parser = subparsers.add_parser(
        'register_paper',
        help=("Register papers given a list of papers ID")
    )
    register_paper_parser.add_argument(
        'input_csv_file_path',
        help='Selected papers ID file path (CSV file path which has "pid" column)'
    )
    register_paper_parser.add_argument(
        'output_file_path',
        help='jsonl output file path'
    )
    register_paper_parser.add_argument(
        '--skip_update',
        type=bool,
        default=False,
        help='True to skip if paper is already registered'
    )

    args = parser.parse_args()

    if args.command == 'register_paper_part':
        register_paper_part(
            args.part_name,
            args.input_csv_file_path,
            args.output_file_path,
            args.skip_update,
            args.pids_selection_file_path,
        )
    elif args.command == 'merge_parts':
        csv_rows_to_json(
            args.input_csv_file_path,
            args.output_file_path,
            args.split_into_n_papers,
        )
    elif args.command == 'register_paper':
        json_to_paper(
            args.input_csv_file_path,
            args.output_file_path,
            args.skip_update,
        )
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
