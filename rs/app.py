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


def receive_new_paper(paper_data):
    """
    Cria paper
    Adiciona as recomendações e outros relacionamentos
    """
    try:
        registered_paper = controller.create_paper(**paper_data)
    except Exception as e:
        return {
            "msg": "Unable to register paper",
            "paper": paper_data,
            "exception": str(e),
        }
    else:
        # adiciona links
        return _find_and_add_related_papers_to_registered_paper(registered_paper)


def receive_paper(paper_data):
    """
    Cria ou atualiza paper
    Adiciona as recomendações e outros relacionamentos
    """
    # cria ou atualiza paper
    result = register_paper(paper_data)
    registered_paper = result.get('registered_paper')

    if not registered_paper:
        return result
    return _find_and_add_related_papers_to_registered_paper(registered_paper)


def register_paper(paper_data):
    """
    Cria ou atualiza paper
    """
    try:
        registered_paper = controller.create_paper(**paper_data)
    except Exception as e:
        try:
            registered_paper = controller.get_paper_by_pid(paper_data['pid'])
        except Exception as e:
            return {
                "msg": "Unable to get registered paper",
                "paper": paper_data,
                "exception": str(e),
            }
        else:
            registered_paper = controller.update_paper(
                registered_paper, **paper_data)
    return {"registered_paper": registered_paper}


def search_papers(text, subject_area, from_year, to_year):
    words = text.split()
    selected_ids = set()
    for word in words:
        _ids = papers_selection.select_papers_by_metadata(
            word, subject_area,
            from_year, to_year,
        )
        selected_ids |= set(_ids)
    if not selected_ids:
        data = dict(
            text=text,
            subject_area=subject_area,
            from_year=from_year,
            to_year=to_year,
        )
        data = {
            k: v for k, v in data.items() if v
        }
        return {
            "msg": "Unable to get selected ids for %s" % data
        }
    links = recommender.find_paper_links(text, selected_ids)

    items = []
    for item in links.get("recommended") or []:
        paper = controller.get_paper_by_record_id(item['paper_id'])
        _item = {}
        _item.update(paper.as_dict())
        _item['score'] = item['score']
        items.append(_item)

    response = {
        "text": text,
        "recommended": items,
    }
    return response


def get_paper_links(pid):
    return controller.get_paper_links(pid)


def find_and_update_related_papers_to_registered_paper(pid):
    response = {}
    response['register_paper'] = controller.get_paper_by_pid(pid)
    response.update(
        _find_and_add_related_papers_to_registered_paper(
            response['register_paper'])
    )
    return response


def _find_and_add_related_papers_to_registered_paper(registered_paper):
    if not registered_paper:
        return {
            "msg": "Unable to get links: missing registered_paper parameter",
        }

    # select ids
    selected_ids = (
        papers_selection.select_papers_which_have_references_in_common(
            registered_paper
        )
    )
    if not selected_ids:
        return {
            "msg": "Unable to get selected ids for registered paper %s" %
                   registered_paper._id,
        }

    # find links
    papers = recommender.find_links_for_registered_paper(
        registered_paper,
        selected_ids,
    )
    # adiciona links
    return controller.register_paper_links(
        registered_paper,
        papers.get('recommended'),
        papers.get('rejected'),
        papers.get('selected_ids'),
    )


def display_pretty(response):
    print(json.dumps(response, indent=2))


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

    get_paper_links_parser = subparsers.add_parser(
        "get_paper_links",
        help=(
            "Get paper links"
        )
    )
    get_paper_links_parser.add_argument(
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
            response = receive_paper(paper_data)
        display_pretty(response)

    elif args.command == "search_papers":
        response = search_papers(
            args.text, args.subject_area, args.from_year, args.to_year)
        display_pretty(response)

    elif args.command == "get_paper_links":
        response = get_paper_links(args.pid)
        display_pretty(response)

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
