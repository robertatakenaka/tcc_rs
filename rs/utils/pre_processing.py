

def is_recommendable_document(document):
    return any([
        document.abstracts,
        document.keywords,
        document.article_titles,
        document.references,
		]
    )
