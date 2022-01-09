from rs.core import (
    controller,
    recommender,
)
from rs import configuration


if not configuration.DATABASE_CONNECT_URL:
    raise ValueError("Missing DATABASE_CONNECT_URL")

controller.db_connect(configuration.DATABASE_CONNECT_URL)


def receive_paper(paper_data, function_to_select_papers_for_semantic_search=None):
    result = register_paper(paper_data)
    registered_paper = result.get('registered_paper')
    if not registered_paper:
        return result

    function_to_select_papers_for_semantic_search = (
        function_to_select_papers_for_semantic_search or
        select_papers_which_have_references_in_common
    )
    selected_ids = function_to_select_papers_for_semantic_search(registered_paper)
    if not selected_ids:
        return result

    semantic_search_parameters = get_params_to_semantic_search(
        registered_paper, selected_ids)
    try:
        papers = compare_papers(**semantic_search_parameters)
    except TypeError:
        papers = {}

    papers['selected_ids'] = selected_ids
    print(papers)
    register_paper_links(
        registered_paper,
        papers.get('recommended'),
        papers.get('rejected'),
        papers.get('selected_ids'),
    )
    return papers


def register_paper(paper_data):
    try:
        registered_paper = controller.create_paper(**paper_data)
    except Exception as e:
        return {
            "msg": "Unable to register paper",
            "paper": paper_data,
            "exception": str(e),
        }
        
        # try:
        #     registered_paper = controller.db.get_records(
        #         controller.Paper, **{'pid': paper_data['pid']})[0]
        # except Exception as e:

        #     return {
        #         "msg": "Unable to register paper",
        #         "paper": paper_data,
        #         "exception": str(e),
        #     }
    return {"registered_paper": registered_paper}


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


def get_params_to_semantic_search(registered_paper, paper_ids):
    """
    Obtém seus textos de seus respectivos ids

    Parameters
    ----------
    paper_ids: str list
        lista de ids de uma seleção de papers

    Returns
    -------
    dict
        keys: text, ids, texts

    """
    parameters = {}
    
    if not paper_ids:
        return parameters

    # obtém os textos dos artigos
    parameters['ids'], parameters['texts'] = (
        controller.get_texts_for_semantic_search(paper_ids)
    )
    if parameters['texts']:
        parameters['text'] = (
            controller.get_text_for_semantic_search(registered_paper)
        )
    return parameters


def compare_papers(text, ids, texts):
    """
    Identifica os papers mais e menos similares

    Parameters
    ----------
    text: str
        texto principal
    ids: str list
        ids dos papers para comparar
    texts: str lisg
        textos dos papers para comparar

    Returns
    -------
    dict
        keys: recommended, rejected

    """
    # se necessario
    # reduz a quantidade de candidatos para minimizar problemas de desempenho
    if len(ids) > configuration.MAX_CANDIDATES:
        ids = ids[-configuration.MAX_CANDIDATES:]
        texts = texts[-configuration.MAX_CANDIDATES:]
        # ids = controller.get_most_recent_paper_ids(ids)[:configuration.MAX_CANDIDATES]

    items = recommender.compare_texts(text, ids, texts)
    response = {}
    response['recommended'] = []
    response['rejected'] = []
    for item in items:
        if item['score'] > float(configuration.MIN_SCORE):
            response['recommended'].append(item)
        else:
            response['rejected'].append(item)
    print(response)
    return response


def register_paper_links(registered_paper, recommended, rejected, linked_by_refs):
    """
    Register links
    """
    # registra os resultados na base de dados
    if recommended:
        controller.register_recommendations(registered_paper, recommended)
    if rejected:
        controller.register_rejections(registered_paper, rejected)
    if linked_by_refs:
        controller.register_linked_by_refs(registered_paper, linked_by_refs)
