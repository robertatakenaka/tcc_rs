import argparse
import csv

from xlingual_papers_recommender.db.data_models import Source, Paper
from xlingual_papers_recommender.db import db


def get_records(DataModelClass):
    items_per_page = 50

    page = 0
    while True:
        page += 1
        skip = ((page - 1) * items_per_page)
        limit = items_per_page
        items = DataModelClass.objects().skip(skip).limit(limit)
        try:
            items[0]
        except IndexError:
            break
        else:
            yield from items


def _get_score_range(score):
    # 'score_gt_89',
    # 'score_gt_79', 'score_gt_69', 'score_gt_59', 'score_gt_1_59',
    # 'score_none',
    if not score:
        return 'score_none'
    if score > 0.89:
        return 'score_gt_89'
    if score > 0.79:
        return 'score_gt_79'
    if score > 0.69:
        return 'score_gt_69'
    if score > 0.59:
        return 'score_gt_59'
    if score < 0.01:
        return 'score_lt_1'
    return 'score_gt_1_59'


def _eval_scores(connections):
    keys = (
        'score_gt_89',
        'score_gt_79', 'score_gt_69', 'score_gt_59', 'score_gt_1_59', 'score_lt_1',
        'score_none',
    )
    d = {k: 0 for k in keys}
    for item in connections:
        k = _get_score_range(item.score)
        d[k] += 1
    return d


def _eval_langs(abstracts):
    keys = (
        'no_en', 'en_only', 'with_en'
    )
    d = {k: 0 for k in keys}
    langs = [abstract.lang for abstract in abstracts]
    if 'en' in langs:
        if len(langs) == 1:
            d['en_only'] = 1
        else:
            d['with_en'] = 1
    else:
        d['no_en'] = 1
    return d


def create_paper_csv(output_csv_file_path):
    with open(output_csv_file_path, 'w', newline='') as csvfile:
        fieldnames = [
            'pid', 'refs', 'refs_with_doi', 'connections',
            'score_gt_89',
            'score_gt_79', 'score_gt_69', 'score_gt_59', 'score_gt_1_59',
            'score_lt_1',
            'score_none',
            'no_en', 'en_only', 'with_en'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for item in get_records(Paper):
            data = {}
            data['pid'] = item.pid
            data['refs'] = len(item.references)
            data['refs_with_doi'] = len([r for r in item.references if r.doi])
            data['connections'] = len(item.connections)
            data.update(_eval_scores(item.connections))
            data.update(_eval_langs(item.abstracts))
            writer.writerow(data)


def create_connections_csv(output_csv_file_path):
    with open(output_csv_file_path, 'w', newline='') as csvfile:
        fieldnames = [
            'pid', 'c_pid', 'c_score', 'c_score_none',
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for item in get_records(Paper):
            for conn in item.connections:
                data = {}
                data['pid'] = item.pid
                data['c_pid'] = len(conn.pid)
                data['c_score'] = conn.score if conn.score else 0
                data['c_score_none'] = 0 if conn.score else 1
                writer.writerow(data)


def _eval_reflinks_years(reflinks):
    years = [r.year for r in reflinks]
    return {
        'reflinks_year_min': min(years),
        'reflinks_year_max': max(years),
    }


def create_source_csv(output_csv_file_path):
    with open(output_csv_file_path, 'w', newline='') as csvfile:
        fieldnames = [
            '_id', 'doi', 'reflinks', 'ref_type',
            'pub_year',
            'reflinks_year_min',
            'reflinks_year_max',
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for item in get_records(Source):
            data = {}
            data['_id'] = item._id
            data['doi'] = 1 if item.doi else 0
            data['ref_type'] = item.ref_type
            data['pub_year'] = item.pub_year
            data['reflinks'] = len(item.reflinks)
            data.update(_eval_reflinks_years(item.reflinks))
            writer.writerow(data)


def main():
    parser = argparse.ArgumentParser(
        description="Crosslingual Papers Recommender Reports")

    subparsers = parser.add_subparsers(
        title="Commands", metavar="", dest="command",
    )

    papers_report_parser = subparsers.add_parser(
        "papers_report",
        help=(
            "Get papers report"
        )
    )
    papers_report_parser.add_argument(
        "output_file_path",
        help=(
            "/path/papers.csv"
        )
    )

    sources_report_parser = subparsers.add_parser(
        "sources_report",
        help=(
            "Get sources report"
        )
    )
    sources_report_parser.add_argument(
        "output_file_path",
        help=(
            "/path/sources.csv"
        )
    )

    connections_report_parser = subparsers.add_parser(
        "connections_report",
        help=(
            "Get connections report"
        )
    )
    connections_report_parser.add_argument(
        "output_file_path",
        help=(
            "/path/connections.csv"
        )
    )

    all_reports_parser = subparsers.add_parser(
        "all",
        help=(
            "Get all reports"
        )
    )
    all_reports_parser.add_argument(
        "papers_file_path",
        help=(
            "/path/papers.csv"
        )
    )
    all_reports_parser.add_argument(
        "souces_file_path",
        help=(
            "/path/souces.csv"
        )
    )
    all_reports_parser.add_argument(
        "connections_file_path",
        help=(
            "/path/connections.csv"
        )
    )

    args = parser.parse_args()
    if args.command == "papers_report":
        create_paper_csv(args.output_file_path)

    elif args.command == "sources_report":
        create_source_csv(args.output_file_path)

    elif args.command == "connections_report":
        create_connections_csv(args.output_csv_file_path)

    elif args.command == "all":
        create_paper_csv(args.papers_file_path)
        create_source_csv(args.souces_file_path)
        create_connections_csv(args.connections_file_path)

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
