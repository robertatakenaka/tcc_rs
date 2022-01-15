import argparse
import json

from rs.core import (
    controller,
    papers_selection,
    recommender,
)
from rs import configuration
from rs.utils import files_utils


if not configuration.DATABASE_CONNECT_URL:
    raise ValueError("Missing DATABASE_CONNECT_URL")


controller.db_connect(configuration.DATABASE_CONNECT_URL)


def receive_new_paper(
        network_collection, pid, main_lang, doi, pub_year,
        subject_areas,
        paper_titles,
        abstracts,
        keywords,
        references,
        create_sources=None,
        create_links=None
        ):
    """
    Cria paper
    """
    return controller.create_paper(
        network_collection, pid, main_lang, doi, pub_year,
        subject_areas,
        paper_titles,
        abstracts,
        keywords,
        references,
        create_sources,
        create_links,
    )


def update_paper(
        network_collection, pid, main_lang, doi, pub_year,
        subject_areas,
        paper_titles,
        abstracts,
        keywords,
        references,
        create_sources=None,
        create_links=None
        ):
    """
    Atualiza paper
    """
    return controller.update_paper(
        network_collection, pid, main_lang, doi, pub_year,
        subject_areas,
        paper_titles,
        abstracts,
        keywords,
        references,
        create_sources,
        create_links,
    )


def search_papers(text, subject_area, from_year, to_year):
    parameters = papers_selection.select_papers_by_text(
        text, subject_area, from_year, to_year)
    links = recommender.compare_papers(
        text, parameters['ids'], parameters['texts']
    )
    items = []
    for item in links.get("recommended") or []:
        paper = controller.get_paper_by_record_id(item['paper_id'])
        paper_data = configuration.add_uri(paper.as_dict())
        paper_data['score'] = item['score']
        items.append(paper_data)

    response = {
        "text": text,
        "recommendations": items,
    }
    return response


def get_linked_papers_lists(pid):
    return controller.get_linked_papers_lists(pid)


def find_and_update_linked_papers_lists(pid):
    return controller.find_and_add_linked_papers_lists(pid)


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

    get_linked_papers_lists_parser = subparsers.add_parser(
        "get_linked_papers_lists",
        help=(
            "Get paper links"
        )
    )
    get_linked_papers_lists_parser.add_argument(
        "pid",
        help=(
            "pid"
        )
    )

    find_and_update_linked_papers_lists_parser = subparsers.add_parser(
        "find_and_update_linked_papers_lists",
        help=(
            "Update linked papers lists"
        )
    )
    find_and_update_linked_papers_lists_parser.add_argument(
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
        _display_response(response, pretty=False)

    elif args.command == "search_papers":
        response = search_papers(
            args.text, args.subject_area, args.from_year, args.to_year)
        _display_response(response, pretty=False)

    elif args.command == "get_linked_papers_lists":
        response = get_linked_papers_lists(args.pid)
        _display_response(response, pretty=False)

    elif args.command == "find_and_update_linked_papers_lists":
        response = find_and_update_linked_papers_lists(args.pid)
        _display_response(response, pretty=False)

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
