import json

from rs.models.models import (
    Article, Reference, SReference, ISSN, DOI, Author, TextAndLang,
)


def json2doc(json_file_path):
    with open(json_file_path) as fp:
        data = json.loads(fp.read())
    return data2doc(data)


def data2doc(data):
    _doc = Article()

    _data = data.get("articles")[0]
    _doc.collection = _data["collection"]
    _doc.id = _data.get("pid") or _data.get("key")

    _issn = ISSN()
    _issn.type = "scielo-id"
    _issn.value = _data["issn"]
    _doc.issns = [_issn]

    _doc.pub_year = _data.get("pubdate")[:4]

    _doc.volume = _data.get("vol")
    _doc.number = _data.get("num")
    _doc.suppl = _data.get("suppl")
    _doc.elocation = _data.get("elocation")
    _doc.fpage = _data.get("fpage")
    _doc.fpage_seq = _data.get("fpage_seq")
    _doc.lpage = _data.get("lpage")

    doi = DOI()
    if _data.get("doi"):
        doi.lang = _data.get("value")
        doi.value = _data.get("doi")
        doi.creation_status = 'assigned_by_editor'
    _doc.doi_with_lang = [doi]

    # contrib = Author()
    # contrib.surname = _data.get("")
    # contrib.given_names = _data.get("")
    # contrib.orcid = _data.get("")

    items = []
    for item in data.get("article_titles"):
        _item = TextAndLang()
        _item.lang = item.get("lang")
        _item.text = item.get("text")
        items.append(_item)
    _doc.article_titles = items

    items = []
    for item in data.get("abstracts"):
        _item = TextAndLang()
        _item.lang = item.get("lang")
        _item.text = item.get("text")
        items.append(_item)
    _doc.abstracts = items

    items = []
    for item in data.get("keywords"):
        _item = TextAndLang()
        _item.lang = item.get("lang")
        _item.text = item.get("text")
        items.append(_item)
    _doc.keywords = items

    items = []
    for item in data.get("references"):
        _item = data2reference(item)
        items.append(_item)
    _doc.references = items

    return _doc


def data2reference(data):
    reference = Reference()
    try:
        reference.pub_year = data.get("pub_date")[:4]
    except:
        pass
    reference.vol = data.get("vol")
    reference.num = data.get("num")
    reference.suppl = data.get("suppl")
    reference.page = data.get("page")
    reference.surname = data.get("surname")
    reference.corpauth = data.get("corpauth")
    reference.doi = data.get("doi")
    reference.journal = data.get("journal")
    reference.article_title = data.get("pub_date")
    reference.source = data.get("source")
    reference.issn = data.get("issn")
    reference.thesis_date = data.get("thesis_date")
    reference.thesis_loc = data.get("thesis_loc")
    reference.thesis_country = data.get("thesis_country")
    reference.thesis_degree = data.get("thesis_degree")
    reference.thesis_org = data.get("thesis_org")
    reference.conf_date = data.get("conf_date")
    reference.conf_loc = data.get("conf_loc")
    reference.conf_country = data.get("conf_country")
    reference.conf_name = data.get("conf_name")
    reference.conf_org = data.get("conf_org")
    reference.publisher_loc = data.get("publisher_loc")
    reference.publisher_country = data.get("publisher_country")
    reference.publisher_name = data.get("publisher_name")
    reference.edition = data.get("edition")
    reference.source_author = data.get("source_author")
    reference.source_corpauth = data.get("source_corpauth")
    return reference


def data2sref(data, article_id):
    reference = SReference()
    try:
        reference.pub_year = data.get("pub_date")[:4]
    except:
        pass
    reference.vol = data.get("vol")
    reference.page = data.get("page")
    reference.surname = data.get("surname")
    reference.corpauth = data.get("corpauth")
    reference.doi = data.get("doi")
    reference.journal = data.get("journal")
    reference.article_title = data.get("pub_date")
    reference.source = data.get("source")

    if not reference.articles:
        reference.articles = []
    reference.articles.append(article_id)
    return reference
