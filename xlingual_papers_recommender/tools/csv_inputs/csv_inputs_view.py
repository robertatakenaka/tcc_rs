import logging
import argparse
import json
import csv
import os
from datetime import datetime
from xlingual_papers_recommender.core import tasks


def ingress_csv(data_label, fieldnames, input_csv_file_path, output_file_path):
    """
    Lê um arquivo CSV que contém um dos dados de artigo, por exemplo:
    references, langs, abstracts, ... e insere este dado no arquivo JSON
    do artigo correspondente
    """

    with open(output_file_path, "w") as fp:
        fp.write("")

    with open(input_csv_file_path, "r") as csvfile:
        reader = csv.DictReader(csvfile, fieldnames=fieldnames)
        for row in reader:
            try:
                row['name'] = data_label
                ret = tasks.register_csv_row_data(row)
            except KeyError as e:
                ret = {"error": "Missing pid %s" % str(row)}
            except ValueError as e:
                ret = row
            except Exception as e:
                ret = {"error": "Ingress csv. Unexpected error %s %s" % (str(row), e)}

            with open(output_file_path, "a") as fp:
                try:
                    s = json.dumps(ret)
                except Exception as e:
                    print(e)
                    print(ret)
                else:
                    fp.write(f"{s}\n")


def csv_rows_to_json(input_csv_file_path, output_file_path, fieldnames, create_paper=False):
    """
    Lê um arquivo CSV que contém um dos dados de artigo, por exemplo:
    references, langs, abstracts, ... e insere este dado no arquivo JSON
    do artigo correspondente
    """

    with open(output_file_path, "w") as fp:
        fp.write("")

    with open(input_csv_file_path, "r") as csvfile:
        reader = csv.DictReader(csvfile, fieldnames=fieldnames)
        for row in reader:
            try:
                pid = row["pid"]
                ret = tasks.csv_rows_to_json(pid, create_paper)
            except KeyError as e:
                ret = {"error": "Missing pid %s" % str(row)}
            except ValueError as e:
                ret = row
            except Exception as e:
                ret = {"error": "Create json from csv. Unexpected error %s %s" % (str(row), e)}

            with open(output_file_path, "a") as fp:
                try:
                    s = json.dumps(ret)
                except Exception as e:
                    print(e)
                    print(ret)
                else:
                    fp.write(f"{s}\n")


def json_to_paper(input_csv_file_path, output_file_path, fieldnames):
    """
    Lê um arquivo CSV que contém um dos dados de artigo, por exemplo:
    references, langs, abstracts, ... e insere este dado no arquivo JSON
    do artigo correspondente
    """

    with open(output_file_path, "w") as fp:
        fp.write("")

    with open(input_csv_file_path, "r") as csvfile:
        reader = csv.DictReader(csvfile, fieldnames=fieldnames)
        for row in reader:
            try:
                pid = row["pid"]
                ret = tasks.json_to_paper(pid)
            except KeyError as e:
                ret = {"error": "Missing pid %s" % str(row)}
            except ValueError as e:
                ret = row
            except Exception as e:
                ret = {"error": "Register paper. Unexpected error %s %s" % (str(row), e)}

            with open(output_file_path, "a") as fp:
                try:
                    s = json.dumps(ret)
                except Exception as e:
                    print(e)
                    print(ret)
                else:
                    fp.write(f"{s}\n")


def main():
    parser = argparse.ArgumentParser(description="Migration tool")
    subparsers = parser.add_subparsers(title="Commands", metavar="", dest="command")

    csv_parser = subparsers.add_parser(
        'csv',
        help=("Lê arquivo `*.csv` que contém dados de um artigo"
              " e registra na coleção raw")
    )
    csv_parser.add_argument(
        'item_name',
        choices=["abstracts", "keywords", "paper_titles", "articles", "references"],
        help='item_name'
    )
    csv_parser.add_argument(
        'fieldnames',
        help='fieldnames'
    )
    csv_parser.add_argument(
        'input_csv_file_path',
        help='input_csv_file_path'
    )
    csv_parser.add_argument(
        'output_file_path',
        help='output_file_path'
    )

    csv2json_parser = subparsers.add_parser(
        'csv2json',
        help=("Lê arquivo `*.csv` que contém pid dos artigos")
    )
    csv2json_parser.add_argument(
        'input_csv_file_path',
        help='input_csv_file_path'
    )
    csv2json_parser.add_argument(
        'output_file_path',
        help='output_file_path'
    )
    csv2json_parser.add_argument(
        'fieldnames',
        help='fieldnames'
    )
    csv2json_parser.add_argument(
        '--create_paper',
        type=bool,
        default=False,
        help='create_paper'
    )

    json2paper_parser = subparsers.add_parser(
        'json2paper',
        help=("Lê arquivo `*.csv` que contém pid dos artigos")
    )
    json2paper_parser.add_argument(
        'input_csv_file_path',
        help='input_csv_file_path'
    )
    json2paper_parser.add_argument(
        'output_file_path',
        help='output_file_path'
    )
    json2paper_parser.add_argument(
        'fieldnames',
        help='fieldnames'
    )

    args = parser.parse_args()

    if args.command == 'csv':
        ingress_csv(
            args.item_name,
            args.fieldnames.split(","),
            args.input_csv_file_path,
            args.output_file_path,
        )
    elif args.command == 'csv2json':
        csv_rows_to_json(
            args.input_csv_file_path,
            args.output_file_path,
            args.fieldnames.split(","),
            args.create_paper,
        )
    elif args.command == 'json2paper':
        json_to_paper(
            args.input_csv_file_path,
            args.output_file_path,
            args.fieldnames.split(","),
        )
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
