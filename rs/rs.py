from rs.core import (
    controller,
    papers_selection,
    recommender,
)
from rs import configuration


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
        add_related_papers_to_registered_paper(registered_paper)
        return {"registered_paper": registered_paper}


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
    add_related_papers_to_registered_paper(registered_paper)
    return {"registered_paper": registered_paper}


def add_related_papers_to_registered_paper(registered_paper):
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
    controller.register_paper_links(
        registered_paper,
        papers.get('recommended'),
        papers.get('rejected'),
        papers.get('selected_ids'),
    )


def register_paper(paper_data):
    """
    Cria ou atualiza paper
    """
    try:
        registered_paper = controller.create_paper(**paper_data)
    except Exception as e:
        try:
            registered_paper = controller.db.get_records(
                controller.Paper, **{'pid': paper_data['pid']})[0]
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


def search_papers(text, subject_area,
                  from_year, to_year,
                  ):
    words = text.split()
    selected_ids = set()
    for word in words:
        _ids = papers_selection.select_papers_by_metadata(
            text, subject_area,
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
    return recommender.find_paper_links(text, selected_ids)

