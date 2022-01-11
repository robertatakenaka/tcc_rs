from rs.core import (
    controller,
)


def select_papers_which_have_references_in_common(registered_paper):
    """
    Identifica os papers relacionados por terem referências em comum

    Parameters
    ----------
    registered_paper: rs.db.data_models.Paper

    Returns
    -------
    str list

    """
    # obtém os IDs de papers que tenham referências em comum com o artigo
    return controller.get_papers_ids_linked_by_references(registered_paper)


def select_papers_by_metadata(
        text, subject_area,
        from_year, to_year,
        ):
    page = 1
    items_per_page = 100
    order_by = None

    registered_papers = controller.search_papers(
        text, subject_area,
        from_year, to_year,
        items_per_page, page, order_by,
    )
    ids = set()
    for paper in registered_papers:
        ids |= set(select_papers_which_have_references_in_common(paper))
        ids |= set([paper._id])

    return list(ids)
