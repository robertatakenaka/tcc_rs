DOI_CREATION_STATUS = ('auto_assigned', 'assigned_by_editor', 'UNK')
DOI_REGISTRATION_STATUS = ('registered', 'not_registered', 'UNK')

ISSN_TYPES = ('epub', 'ppub', 'l', 'scielo-id')


def document_as_dict(
        id,
        collection,
        issns, pub_year,
        doi_with_lang,
        authors, collab, article_titles,
        volume, number, suppl, elocation, fpage, fpage_seq, lpage,
        epub_date, filenames,
        related_articles,
        abstracts,
        keywords,
        subject_areas,
        ):
    """
    Retorna um dicionário com os atributos do documento
    """
    return {
        "id": id or '',
        "collection": collection or '',
        "issns": issns or '',
        "pub_year": pub_year or '',
        "doi_with_lang": doi_with_lang or '',
        "authors": authors or '',
        "collab": collab or '',
        "article_titles": article_titles or '',
        "volume": volume or '',
        "number": number or '',
        "suppl": suppl or '',
        "elocation": elocation or '',
        "fpage": fpage or '',
        "fpage_seq": fpage_seq or '',
        "lpage": lpage or '',
        "epub_date": epub_date or '',
        "filenames": filenames or '',
        "related_articles": related_articles or '',
        "abstracts": abstracts or '',
        "keywords": keywords or '',
        "subject_areas": subject_areas or '',
    }


class Document:

    def __init__(self):
        self._id = None
        self._collection = None
        self._issns = None
        self._pub_year = None
        self._doi_with_lang = None
        self._authors = None
        self._collab = None
        self._article_titles = None
        self._volume = None
        self._number = None
        self._suppl = None
        self._elocation = None
        self._fpage = None
        self._fpage_seq = None
        self._lpage = None
        self._epub_date = None
        self._filenames = None
        self._related_articles = None
        self._abstracts = None
        self._keywords = None
        self._subject_areas = None

    @property
    def id(self):
        return self._id

    @property
    def collection(self):
        return self._collection

    @property
    def issns(self):
        return self._issns

    @property
    def pub_year(self):
        return self._pub_year

    @property
    def doi_with_lang(self):
        return self._doi_with_lang

    @property
    def authors(self):
        return self._authors

    @property
    def collab(self):
        return self._collab

    @property
    def article_titles(self):
        return self._article_titles

    @property
    def volume(self):
        return self._volume

    @property
    def number(self):
        return self._number

    @property
    def suppl(self):
        return self._suppl

    @property
    def elocation(self):
        return self._elocation

    @property
    def fpage(self):
        return self._fpage

    @property
    def fpage_seq(self):
        return self._fpage_seq

    @property
    def lpage(self):
        return self._lpage

    @property
    def epub_date(self):
        return self._epub_date

    @property
    def filenames(self):
        return self._filenames

    @property
    def related_articles(self):
        return self._related_articles

    @property
    def abstracts(self):
        return self._abstracts

    @property
    def keywords(self):
        return self._keywords

    @property
    def subject_areas(self):
        return self._subject_areas

    @id.setter
    def id(self, value):
        self._id = value

    @collection.setter
    def collection(self, value):
        self._collection = value

    @issns.setter
    def issns(self, value):
        self._issns = value

    @pub_year.setter
    def pub_year(self, value):
        self._pub_year = value

    @doi_with_lang.setter
    def doi_with_lang(self, value):
        self._doi_with_lang = value

    @authors.setter
    def authors(self, value):
        self._authors = value

    @collab.setter
    def collab(self, value):
        self._collab = value

    @article_titles.setter
    def article_titles(self, value):
        self._article_titles = value

    @volume.setter
    def volume(self, value):
        self._volume = value

    @number.setter
    def number(self, value):
        self._number = value

    @suppl.setter
    def suppl(self, value):
        self._suppl = value

    @elocation.setter
    def elocation(self, value):
        self._elocation = value

    @fpage.setter
    def fpage(self, value):
        self._fpage = value

    @fpage_seq.setter
    def fpage_seq(self, value):
        self._fpage_seq = value

    @lpage.setter
    def lpage(self, value):
        self._lpage = value

    @epub_date.setter
    def epub_date(self, value):
        self._epub_date = value

    @filenames.setter
    def filenames(self, value):
        self._filenames = value

    @related_articles.setter
    def related_articles(self, value):
        self._related_articles = value

    @abstracts.setter
    def abstracts(self, value):
        self._abstracts = value

    @keywords.setter
    def keywords(self, value):
        self._keywords = value

    @subject_areas.setter
    def subject_areas(self, value):
        self._subject_areas = value


