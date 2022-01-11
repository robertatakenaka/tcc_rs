from rs.configuration import ITEMS_PER_PAGE
from rs.core import (
    controller,
)


def get_text_papers_to_compare(selected_ids):
    parameters = {}
    if selected_ids:
        # obtém os textos dos artigos
        parameters['ids'], parameters['texts'] = (
            controller.get_texts_for_semantic_search(selected_ids)
        )
    return parameters


def select_papers_which_have_references_in_common(registered_paper, total_sources):
    """
    Identifica os papers relacionados por terem referências em comum

    Parameters
    ----------
    registered_paper: rs.db.data_models.Paper

    Returns
    -------
    str dict

    """
    return get_text_papers_to_compare(
        controller.get_papers_ids_linked_by_references(
            registered_paper, total_sources)
    )


def _select_papers_by_word(
        text, subject_area,
        from_year, to_year,
        page=None, items_per_page=None, order_by=None,
        ):
    page = page or 1
    items_per_page = items_per_page or ITEMS_PER_PAGE
    order_by = order_by or '-pub_year'

    registered_papers = controller.search_papers(
        text, subject_area,
        from_year, to_year,
        items_per_page, page, order_by,
    )
    ids = set()
    for paper in registered_papers:
        ids |= set(controller.get_papers_ids_linked_by_references(paper))
        ids |= set([paper._id])

    return ids


def select_papers_by_text(
        text, subject_area=None, from_year=None, to_year=None,
        page=None, items_per_page=None, order_by=None,
        ):
    page = page or 1
    items_per_page = items_per_page or ITEMS_PER_PAGE
    order_by = order_by or '-pub_year'

    # FIXME
    words = set(text.split())
    selected_ids = set()
    for word in words:
        _ids = _select_papers_by_word(
            word, subject_area,
            from_year, to_year,
            items_per_page, page, order_by,
        )
        selected_ids |= set(_ids)
    return get_text_papers_to_compare(list(selected_ids))
