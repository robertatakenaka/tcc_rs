import argparse

from rs.utils import sentences_transformations
# import os
# import json
# import csv


def mini(words):
    sentences_transformations.try_models(words.split(" "))


def compare_vectors(input_file_path, output_folder_path):
    pass


def gen_vector(input_file_path, output_folder_path):
    pass


def main():
    parser = argparse.ArgumentParser(description='Group article data')
    subparsers = parser.add_subparsers(
        title='Command', metavar='', dest='command')

    gen_vector_parser = subparsers.add_parser(
        'gen_vector',
        help=("Lê arquivos vários `*.csv` que contém dados de um artigo"
              " e cria um único arquivo `<pid>.json` por artigo")
    )
    gen_vector_parser.add_argument(
        'input_csv_file_path',
        help='input_csv_file_path'
    )
    gen_vector_parser.add_argument(
        'output_folder_path',
        help='output_folder_path'
    )

    compare_vectors_parser = subparsers.add_parser(
        'compare_vectors',
        help=("Lê arquivos vários `*.csv` que contém dados de um artigo"
              " e cria um único arquivo `<pid>.json` por artigo")
    )
    compare_vectors_parser.add_argument(
        'input_csv_file_path',
        help='input_csv_file_path'
    )
    compare_vectors_parser.add_argument(
        'output_folder_path',
        help='output_folder_path'
    )

    mini_parser = subparsers.add_parser(
        'mini',
        help=("Lê arquivos vários `*.csv` que contém dados de um artigo"
              " e cria um único arquivo `<pid>.json` por artigo")
    )
    mini_parser.add_argument(
        'words',
        help='words'
    )

    args = parser.parse_args()

    if args.command == 'mini':
        mini(args.words)
    elif args.command == 'compare_vectors':
        compare_vectors(args.input_csv_file_path, args.output_folder_path)
    elif args.command == 'gen_vector':
        gen_vector(args.input_csv_file_path, args.output_folder_path)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
