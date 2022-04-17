import logging
import argparse
import json
import csv
import os
from datetime import datetime
from xlingual_papers_recommender.tools.csv_inputs import tasks


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
                ret = tasks.register_row(row)
            except ValueError:
                ret = row
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
        choices=["abstracts", "keywords", "titles", "article", "references"],
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

    args = parser.parse_args()

    if args.command == 'csv':
        ingress_csv(
            args.item_name,
            args.fieldnames.split(","),
            args.input_csv_file_path,
            args.output_file_path,
        )
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
