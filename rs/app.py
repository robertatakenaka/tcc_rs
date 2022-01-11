import argparse
import json

from rs.core import (
    controller,
    papers_selection,
    recommender,
    tasks,
)
from rs import configuration, exceptions
from rs.utils import files_utils


if not configuration.DATABASE_CONNECT_URL:
    raise ValueError("Missing DATABASE_CONNECT_URL")


controller.db_connect(configuration.DATABASE_CONNECT_URL)


def receive_new_paper(paper_data):
    """
    Cria paper
    Adiciona as recomendações e outros relacionamentos
    """
    try:
        print("Receive new paper")
        response = controller.create_paper(**paper_data)
    except Exception as e:
        return exceptions.add_exception({
            "error": "Unable to register paper",
            "paper": paper_data},
            e,
        )
    else:
        registered_paper = response.get("registered_paper")
        total_sources = response.get("total sources")
        if total_sources:
            # adiciona links
            print("Find and add linked papers")
            _find_and_add_linked_papers_lists(registered_paper, total_sources)
        return {"linked_paper": "created"}


def update_paper(paper_data):
    """
    Atualiza paper
    Adiciona as recomendações e outros relacionamentos
    """
    try:
        print("Update paper")
        registered_paper = controller.get_paper_by_pid(paper_data['pid'])
        response = controller.update_paper(registered_paper, **paper_data)
    except Exception as e:
        return exceptions.add_exception({
            "error": "Unable to get registered paper",
            "paper": paper_data,
            },
            e,
        )
    else:
        registered_paper = response.get("registered_paper")
        total_sources = response.get("total sources")
        if total_sources:
            # adiciona links
            print("Find and add linked papers")
            _find_and_add_linked_papers_lists(registered_paper, total_sources)
        return {"linked_paper": "updated"}


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
    response = {}
    response['register_paper'] = controller.get_paper_by_pid(pid)
    response.update(
        _find_and_add_linked_papers_lists(
            response['register_paper']
        )
    )
    return response


def _find_and_add_linked_papers_lists(registered_paper, total_sources=None):
    if not registered_paper:
        return {
            "error": "Unable to get linked papers: missing registered_paper parameter",
        }

    # select ids
    parameters = (
        papers_selection.select_papers_which_have_references_in_common(
            registered_paper, total_sources
        )
    )
    if not parameters:
        return {
            "error": "Unable to get selected ids for registered paper %s" %
            registered_paper._id,
        }

    text = controller.get_text_for_semantic_search(registered_paper)
    response = tasks.compare_texts_and_register_result.apply_async((
            registered_paper._id,
            text,
            parameters['ids'],
            parameters['texts'],
    ))
    # print(response.get())


def display_response(response, pretty=True):
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
            response = receive_new_paper(paper_data)
        else:
            response = update_paper(paper_data)
        display_response(response, pretty=False)

    elif args.command == "search_papers":
        response = search_papers(
            args.text, args.subject_area, args.from_year, args.to_year)
        display_response(response, pretty=False)

    elif args.command == "get_linked_papers_lists":
        response = get_linked_papers_lists(args.pid)
        display_response(response, pretty=False)

    elif args.command == "find_and_update_linked_papers_lists":
        response = find_and_update_linked_papers_lists(args.pid)
        display_response(response, pretty=False)

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
