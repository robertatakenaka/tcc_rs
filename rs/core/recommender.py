
def create_recommendations(document):
    return


def get_recommendations(document):
    selected_documents = get_documents_selection(document)
    ranking = eval_similarity(document, selected_documents)
    return most_similar_documents(ranking)
