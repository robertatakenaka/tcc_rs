from datetime import datetime

from mongoengine import (
    EmbeddedDocument,
    EmbeddedDocumentListField,
    Document,
    StringField,
    ListField,
    DateField,
    DateTimeField,
)

from rs.models import document

# MULTI_VALUE_ATTRIBS = [
#     'issns', 'authors', 'article_titles', 'filenames', 'other_pids',
#     'doi_with_lang',
# ]
# COMPOSE_VALUE_ATTRIBS = dict(
#     issns=ISSN,
#     doi_with_lang=DOI,
#     authors=Author,
#     article_titles=TextAndLang,
#     related_articles=RelatedArticle,
# )


class TextAndLang(EmbeddedDocument):
    lang = StringField()
    text = StringField()

    def __unicode__(self):
        return {"lang": self.lang, "text": self.text}


class DOI(EmbeddedDocument):
    lang = StringField()
    value = StringField()
    creation_status = StringField(choices=document.DOI_CREATION_STATUS)
    registration_status = StringField(choices=document.DOI_REGISTRATION_STATUS)

    def __unicode__(self):
        return {
            "lang": self.lang, "value": self.value,
            "creation_status": self.creation_status,
            "registration_status": self.registration_status,
        }


class ISSN(EmbeddedDocument):
    value = StringField()
    type = StringField(choices=document.ISSN_TYPES)

    def __unicode__(self):
        return {
            "value": self.value,
            "type": self.type,
        }


class Author(EmbeddedDocument):
    surname = StringField()
    given_names = StringField()
    orcid = StringField()

    def __unicode__(self):
        return (
            '%s' %
            {"surname": self.surname, "given_names": self.given_names,
             "orcid": self.orcid, })


class RelatedArticle(EmbeddedDocument):
    """
    Model responsible for relationship between articles.
    Attributes:
    ref_id: String content any reference Id to the article
        pid_v1, pid_v2 or pid_v3
    doi: String content the Crossref Id, if the article dont have DOI use the
    ``ref_id``
    related_type: String with a category of relation.
    Example of this model:
        "related_articles" : [
            {
                "id": "9LzVjQrYQF7BvkYWnJw9sDy",
                "id_type" : "scielo-v3",
                "related_type" : "corrected-article"
            },
            {
                "id": "3LzVjQrOIEJYUSvkYWnJwsDy",
                "id_type" : "doi",
                "related_type" : "addendum"
            },
            {
                "id": "1234",
                "id_type" : "other",
                "related_type" : "retraction"
            },
        ]
    """
    id = StringField()
    id_type = StringField()
    related_type = StringField()

    def __unicode__(self):
        return {
            "id": self.id,
            "id_type": self.id_type,
            "related_type": self.related_type,
        }


class Reference(Document):
    _id = StringField(max_length=32, primary_key=True, required=True)

    pid = StringField()
    collection = StringField()
    pub_year = StringField()
    vol = StringField()
    num = StringField()
    suppl = StringField()
    page = StringField()
    surname = StringField()
    corpauth = StringField()
    doi = StringField()
    journal = StringField()
    article_title = StringField()
    source = StringField()
    issn = StringField()
    thesis_date = StringField()
    thesis_loc = StringField()
    thesis_country = StringField()
    thesis_degree = StringField()
    thesis_org = StringField()
    conf_date = StringField()
    conf_loc = StringField()
    conf_country = StringField()
    conf_name = StringField()
    conf_org = StringField()
    publisher_loc = StringField()
    publisher_country = StringField()
    publisher_name = StringField()
    edition = StringField()
    source_author = StringField()
    source_corpauth = StringField()

    # datas deste registro
    created = DateTimeField()
    updated = DateTimeField()

    meta = {
        'collection': 'pid_manager',
        'indexes': [
            'pid',
            'collection',
            'pub_year',
            'vol',
            'num',
            'suppl',
            'page',
            'surname',
            'corpauth',
            'doi',
            'journal',
            'article_title',
            'source',
            'issn',
            'thesis_date',
            'thesis_loc',
            'thesis_country',
            'thesis_degree',
            'thesis_org',
            'conf_date',
            'conf_loc',
            'conf_country',
            'conf_name',
            'conf_org',
            'publisher_loc',
            'publisher_country',
            'publisher_name',
            'edition',
            'source_author',
            'source_corpauth',
        ]
    }

    def save(self, *args, **kwargs):
        if not self.created:
            self.created = datetime.utcnow().isoformat().replace("T", " ")
        self.updated = datetime.utcnow().isoformat().replace("T", " ")

        return super(Reference, self).save(*args, **kwargs)


class SReference(Document):
    _id = StringField(max_length=32, primary_key=True, required=True)

    doi = StringField()
    pub_year = StringField()
    surname = StringField()
    corpauth = StringField()

    source = StringField()
    other = StringField()

    article_title = StringField()
    journal = StringField()
    vol = StringField()
    page = StringField()

    articles = ListField(StringField())

    # datas deste registro
    created = DateTimeField()
    updated = DateTimeField()

    meta = {
        'collection': 'pid_manager',
        'indexes': [
            'doi',
            'pub_year',
            'vol',
            'page',
            'surname',
            'corpauth',
            'journal',
            'article_title',
            'source',
        ]
    }

    def save(self, *args, **kwargs):
        if not self.created:
            self.created = datetime.utcnow().isoformat().replace("T", " ")
        self.updated = datetime.utcnow().isoformat().replace("T", " ")

        return super(Reference, self).save(*args, **kwargs)


class Article(Document):
    _id = StringField(max_length=32, primary_key=True, required=True)
    collection = StringField()
    id = StringField(max_length=23, unique=True, required=True)

    issns = EmbeddedDocumentListField(ISSN)
    pub_year = StringField()

    doi_with_lang = EmbeddedDocumentListField(DOI)
    authors = EmbeddedDocumentListField(Author)
    collab = StringField()

    article_titles = EmbeddedDocumentListField(TextAndLang)
    abstracts = EmbeddedDocumentListField(TextAndLang)
    keywords = EmbeddedDocumentListField(TextAndLang)
    references = EmbeddedDocumentListField(Reference)

    volume = StringField()
    number = StringField()
    suppl = StringField()
    elocation = StringField()
    fpage = StringField()
    fpage_seq = StringField()
    lpage = StringField()

    related_articles = EmbeddedDocumentListField(RelatedArticle)

    epub_date = DateField()

    # datas deste registro
    created = DateTimeField()
    updated = DateTimeField()

    meta = {
        'collection': 'pid_manager',
        'indexes': [
            'collection',
            'id',
            'issns',
            'doi_with_lang',
            'pub_year',
            'authors',
            'volume',
            'number',
            'suppl',
            'elocation',
            'fpage',
            'fpage_seq',
            'lpage',
        ]
    }

    def save(self, *args, **kwargs):
        if not self.created:
            self.created = datetime.utcnow().isoformat().replace("T", " ")
        self.updated = datetime.utcnow().isoformat().replace("T", " ")

        return super(Article, self).save(*args, **kwargs)
