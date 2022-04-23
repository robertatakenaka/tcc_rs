import logging
import argparse
import json
import os
from datetime import datetime

from xlingual_papers_recommender.core import tasks, controller
from xlingual_papers_recommender.utils import files_utils


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
    inclusion_list = list(files_utils.read_csv_file(pids_selection_file_path))

    with open(output_file_path, "w") as fp:
        fp.write("")

    for row in files_utils.read_csv_file(input_csv_file_path):
        try:
            if len(row["pid"]) == 28:
                row["ref_pid"] = row["pid"]
                row["pid"] = row["pid"][:23]
                row["lang"] = row["ref_pid"]
            row['name'] = part_name
            if not inclusion_list or row['pid'] in inclusion_list:
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
            pid = row["pid"]
            response = tasks.csv_rows_to_json(pid, split)
        except KeyError as e:
            response = {"error": "Missing pid %s" % str(row)}
        except ValueError as e:
            response = row
        except Exception as e:
            response = {"error": "Create json from csv. Unexpected error %s %s" % (str(row), e)}

        write_output_file(output_file_path, response)


def json_to_paper(input_csv_file_path, output_file_path):
    """
    Lê um arquivo CSV que contém um dos dados de artigo, por exemplo:
    references, langs, abstracts, ... e insere este dado no arquivo JSON
    do artigo correspondente
    """

    with open(output_file_path, "w") as fp:
        fp.write("")

    for row in files_utils.read_csv_file(input_csv_file_path):
        try:
            pid = row["pid"]
            response = controller.json_to_paper(pid)
        except KeyError as e:
            response = {"error": "Missing pid %s" % str(row)}
        except ValueError as e:
            response = row
        except Exception as e:
            response = {"error": "Register paper. Unexpected error %s %s" % (str(row), e)}

        write_output_file(output_file_path, response)


def main():
    parser = argparse.ArgumentParser(description="Input tools")
    subparsers = parser.add_subparsers(title="Commands", metavar="", dest="command")

    register_paper_part_parser = subparsers.add_parser(
        'register_paper_part',
        help=("Lê arquivo `*.csv` que contém dados de um artigo"
              " e registra na coleção csv_row")
    )
    register_paper_part_parser.add_argument(
        'part_name',
        choices=["abstracts", "references", "keywords", "paper_titles", "articles"],
        help='part_name'
    )
    register_paper_part_parser.add_argument(
        'input_csv_file_path',
        help='input_csv_file_path'
    )
    register_paper_part_parser.add_argument(
        'output_file_path',
        help='output_file_path'
    )
    register_paper_part_parser.add_argument(
        '--skip_update',
        type=bool,
        default=False,
        help='skip_update'
    )
    register_paper_part_parser.add_argument(
        '--pids_selection_file_path',
        default=None,
        help='pids_selection_file_path'
    )

    merge_parts_parser = subparsers.add_parser(
        'merge_parts',
        help=("Une os componentes do artigo")
    )
    merge_parts_parser.add_argument(
        'input_csv_file_path',
        help='input_csv_file_path'
    )
    merge_parts_parser.add_argument(
        'output_file_path',
        help='output_file_path'
    )
    merge_parts_parser.add_argument(
        '--split_into_n_papers',
        default=None,
        help='split_into_n_papers'
    )
    merge_parts_parser.add_argument(
        '--create_paper',
        type=bool,
        default=False,
        help='create_paper'
    )

    register_paper_parser = subparsers.add_parser(
        'register_paper',
        help=("Lê arquivo `*.csv` que contém pid dos artigos")
    )
    register_paper_parser.add_argument(
        'input_csv_file_path',
        help='input_csv_file_path'
    )
    register_paper_parser.add_argument(
        'output_file_path',
        help='output_file_path'
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
            args.create_paper,
        )
    elif args.command == 'register_paper':
        json_to_paper(
            args.input_csv_file_path,
            args.output_file_path,
        )
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
