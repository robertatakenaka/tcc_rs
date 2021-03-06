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


def _min_and_max_scores(connections):
    scores = [
        item.score for item in connections
    ]
    score_none = scores.count(None)

    data = {
        "connections_without_score": score_none,
        "connections_with_score": len(connections) - score_none,
    }

    while None in scores:
        scores.remove(None)

    if scores:
        data.update(
            {"max_score": max(scores), "min_score": min(scores)}
        )
    return data


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


def create_paper_refs_csv(output_csv_file_path):
    with open(output_csv_file_path, 'w', newline='') as csvfile:
        fieldnames = [
            'pid', 
            'refs', 'refs_with_doi', 'refs_without_doi',
            'connections', 'connections_with_score', 'connections_without_score',
            'min_score',
            'max_score',
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for item in get_records(Paper):
            total_refs = len(item.references)
            refs_with_doi = len([r for r in item.references if r.doi])
            refs_without_doi = total_refs - refs_with_doi

            data = {}
            data['pid'] = item.pid
            data['refs'] = total_refs
            data['refs_without_doi'] = refs_without_doi
            data['refs_with_doi'] = refs_with_doi
            data['connections'] = len(item.connections)
            data.update(_min_and_max_scores(item.connections))
            writer.writerow(data)


def create_connections_csv(output_csv_file_path):
    with open(output_csv_file_path, 'w', newline='') as csvfile:
        fieldnames = [
            'a_pid', 'c_pid', 'real_a_pid', 'real_c_pid', 'same',
            'c_score', 'c_score_none',
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for item in get_records(Paper):
            for conn in item.connections:
                data = {}
                data['a_pid'] = item.pid
                data['c_pid'] = conn.pid
                data['real_a_pid'] = item.pid[:23]
                data['real_c_pid'] = conn.pid[:23]
                data['same'] = 1 if data['real_a_pid'] == data['real_c_pid'] else 0
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


def create_source_refs_csv(output_csv_file_path):
    with open(output_csv_file_path, 'w', newline='') as csvfile:
        fieldnames = [
            'source_id', 'doi', 'reflinks', 'ref_type',
            'pub_year',
            'pid',
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for item in get_records(Source):
            for ref in item.reflinks:
                data = {}
                data['source_id'] = item._id
                data['doi'] = 1 if item.doi else 0
                data['ref_type'] = item.ref_type
                data['pub_year'] = item.pub_year
                data['reflinks'] = len(item.reflinks)
                data['pid'] = ref.pid
                writer.writerow(data)


def main():
    parser = argparse.ArgumentParser(description="Recommender System reports")
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

    papers_refs_report_parser = subparsers.add_parser(
        "papers_refs_report",
        help=(
            "Get papers refs report"
        )
    )
    papers_refs_report_parser.add_argument(
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

    sources_refs_report_parser = subparsers.add_parser(
        "sources_refs_report",
        help=(
            "Get sources report"
        )
    )
    sources_refs_report_parser.add_argument(
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
            "Generate all reports: papers, sources, connections, papers_refs, sources_refs"
        )
    )
    all_reports_parser.add_argument(
        "reports_path",
        help=(
            "/path"
        )
    )

    args = parser.parse_args()
    if args.command == "papers_report":
        create_paper_csv(args.output_file_path)

    elif args.command == "papers_refs_report":
        create_paper_refs_csv(args.output_file_path)

    elif args.command == "sources_report":
        create_source_csv(args.output_file_path)

    elif args.command == "sources_refs_report":
        create_source_refs_csv(args.output_file_path)

    elif args.command == "connections_report":
        create_connections_csv(args.output_csv_file_path)

    elif args.command == "all":
        papers_file_path = os.path.join(args.reports_path, "papers.csv")
        sources_file_path = os.path.join(args.reports_path, "sources.csv")
        connections_file_path = os.path.join(args.reports_path, "connections.csv")
        papers_refs_file_path = os.path.join(args.reports_path, "papers_refs.csv")
        sources_refs_file_path = os.path.join(args.reports_path, "sources_refs.csv")

        create_paper_csv(papers_file_path)
        create_source_csv(souces_file_path)
        create_connections_csv(connections_file_path)
        create_sources_refs_csv(sources_refs_file_path)
        create_papers_refs_csv(papers_refs_file_path)

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
