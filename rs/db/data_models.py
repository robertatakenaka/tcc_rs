from rs.configuration import handle_text_s

from datetime import datetime

from mongoengine import (
    EmbeddedDocument,
    EmbeddedDocumentListField,
    Document,
    StringField,
    ListField,
    DateTimeField,
    DecimalField,
)

"""
NA = NOT APPLICABLE - has no text and has no references
SOURCE_REGISTERED = created source from reference data
LINKS_TODO = there are references in common / there are possibly similar
LINKS_DONE = it was possible to find similar documents
"""
RS_PROC_STATUS = ("NA", "SOURCE_REGISTERED", "LINKS_TODO", "LINKS_DONE")

DOI_CREATION_STATUS = ('auto_assigned', 'assigned_by_editor', 'UNK')
DOI_REGISTRATION_STATUS = ('registered', 'not_registered', 'UNK')
ISSN_TYPES = ('epub', 'ppub', 'l', 'scielo-id')


PROC_STATUS_NA = RS_PROC_STATUS[0]
PROC_STATUS_SOURCE_REGISTERED = RS_PROC_STATUS[1]
PROC_STATUS_TODO = RS_PROC_STATUS[2]
PROC_STATUS_DONE = RS_PROC_STATUS[3]


def utcnow():
    return datetime.utcnow()


def paper_summary(obj):
    data = {
        "uri_params": _paper_uri_params(obj),
        "pub_year": obj.pub_year,
        "doi_with_lang": [item.as_dict() for item in obj.doi_with_lang],
        "paper_titles": [item.as_dict() for item in obj.paper_titles],
        "abstracts": [item.as_dict() for item in obj.abstracts],
    }
    if hasattr(obj, 'score') and obj.score:
        data['score'] = float(obj.score)
    return data


def _paper_uri_params(paper):
    """
    "uri_params": {
        "pid": obj.pid,
        "collection_id": obj.network_collection,
    }
    """
    try:
        url = CollectionWebsite.objects(acron=paper.network_collection)[0].url
    except:
        url = "www.meusite.org"
    return {"url": url, "id": paper.pid}


def _create_linked_paper(paper, score=None):
    item = Recommendation()
    item.pid = paper.pid
    item.network_collection = paper.network_collection
    item.pub_year = paper.pub_year
    item.doi_with_lang = paper.doi_with_lang
    item.paper_titles = paper.paper_titles
    item.abstracts = paper.abstracts
    if score:
        item.score = score
    return item


class TextAndLang(EmbeddedDocument):
    lang = StringField()
    text = StringField()

    def as_dict(self):
        return {"lang": self.lang, "text": self.text}

    def __str__(self):
        return self.to_json()


class DOI(EmbeddedDocument):
    lang = StringField()
    value = StringField()
    creation_status = StringField(choices=DOI_CREATION_STATUS)
    registration_status = StringField(choices=DOI_REGISTRATION_STATUS)

    def as_dict(self):
        return {
            "lang": self.lang, "value": self.value,
            "creation_status": self.creation_status,
            "registration_status": self.registration_status,
        }

    def __str__(self):
        return self.to_json()


class ISSN(EmbeddedDocument):
    value = StringField()
    type = StringField(choices=ISSN_TYPES)

    def as_dict(self):
        return {
            "type": self.type,
            "value": self.value,
        }

    def __str__(self):
        return self.to_json()


class Author(EmbeddedDocument):
    surname = StringField()
    given_names = StringField()
    orcid = StringField()

    def as_dict(self):
        return {
            "surname": self.surname,
            "given_names": self.given_names,
            "orcid": self.orcid,
        }

    def __str__(self):
        return self.to_json()


class RelatedPaper(EmbeddedDocument):
    """
    Model responsible for relationship between papers.
    Attributes:
    ref_id: String content any reference Id to the paper
        pid_v1, pid_v2 or pid_v3
    doi: String content the Crossref Id, if the paper dont have DOI use the
    ``ref_id``
    related_type: String with a category of relation.
    Example of this model:
        "related_papers" : [
            {
                "id": "9LzVjQrYQF7BvkYWnJw9sDy",
                "id_type" : "scielo-v3",
                "related_type" : "corrected-paper"
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

    def as_dict(self):
        return {
            "id": self.id,
            "id_type": self.id_type,
            "related_type": self.related_type,
        }

    def __str__(self):
        return self.to_json()


# COMPOSE_VALUE_ATTRIBS = dict(
#     issns=ISSN,
#     doi_with_lang=DOI,
#     authors=Author,
#     paper_titles=TextAndLang,
#     related_papers=RelatedPaper,
#     reference=Reference,
# )


class Recommendation(EmbeddedDocument):
    pid = StringField()
    network_collection = StringField()
    pub_year = StringField()
    doi_with_lang = EmbeddedDocumentListField(DOI)
    paper_titles = EmbeddedDocumentListField(TextAndLang)
    abstracts = EmbeddedDocumentListField(TextAndLang)
    score = DecimalField()

    def as_dict(self):
        return paper_summary(self)

    def __str__(self):
        return self.to_json()


class Reference(EmbeddedDocument):
    pub_year = StringField()
    vol = StringField()
    num = StringField()
    suppl = StringField()
    page = StringField()
    surname = StringField()
    organization_author = StringField()
    doi = StringField()
    journal = StringField()
    paper_title = StringField()
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
    source_person_author_surname = StringField()
    source_organization_author = StringField()

    @property
    def ref_type(self):
        if self.journal:
            return "journal"
        if self.conf_name:
            return "conference"
        if any([self.thesis_degree, self.thesis_date, self.thesis_org, self.thesis_loc, self.thesis_country]):
            return "thesis"
        if self.source:
            return "book"
        return "unidentified"

    @property
    def has_data_enough(self):
        if not self.pub_year:
            return False
        if self.journal and (self.surname or self.organization_author):
            return True
        if self.source:
            return True
        return False

    @property
    def as_dict(self):
        return dict(
            pub_year=self.pub_year,
            vol=self.vol,
            num=self.num,
            suppl=self.suppl,
            page=self.page,
            surname=self.surname,
            organization_author=self.organization_author,
            doi=self.doi,
            journal=self.journal,
            paper_title=self.paper_title,
            source=self.source,
            issn=self.issn,
            thesis_date=self.thesis_date,
            thesis_loc=self.thesis_loc,
            thesis_country=self.thesis_country,
            thesis_degree=self.thesis_degree,
            thesis_org=self.thesis_org,
            conf_date=self.conf_date,
            conf_loc=self.conf_loc,
            conf_country=self.conf_country,
            conf_name=self.conf_name,
            conf_org=self.conf_org,
            publisher_loc=self.publisher_loc,
            publisher_country=self.publisher_country,
            publisher_name=self.publisher_name,
            edition=self.edition,
            source_person_author_surname=self.source_person_author_surname,
            source_organization_author=self.source_organization_author,
        )


class Source(Document):
    pub_year = StringField()
    vol = StringField()
    num = StringField()
    suppl = StringField()
    page = StringField()
    surname = StringField()
    organization_author = StringField()
    doi = StringField()
    journal = StringField()
    paper_title = StringField()
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
    source_person_author_surname = StringField()
    source_organization_author = StringField()
    referenced_by = ListField(StringField())
    ref_type = StringField()

    # datas deste registro
    created = DateTimeField()
    updated = DateTimeField()

    meta = {
        'collection': 'rs_source',
        'indexes': [
            'pub_year',
            'vol',
            'num',
            'suppl',
            'page',
            'surname',
            'organization_author',
            'doi',
            'journal',
            'paper_title',
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
            'source_person_author_surname',
            'source_organization_author',
            'referenced_by',
            'ref_type',
        ]
    }

    def add_referenced_by(self, paper_id):
        str_paper_id = str(paper_id)
        if not self.referenced_by:
            self.referenced_by = []
        if str_paper_id not in self.referenced_by:
            self.referenced_by.append(str_paper_id)

    @property
    def _id(self):
        return str(self.id)

    def get_ref_type(self):
        if self.journal:
            return "journal"
        if self.conf_name:
            return "conference"
        if any([self.thesis_degree, self.thesis_date, self.thesis_org, self.thesis_loc, self.thesis_country]):
            return "thesis"
        if self.source:
            return "book"
        return "unidentified"

    def save(self, *args, **kwargs):
        if not self.created:
            self.created = utcnow()
        self.updated = utcnow()
        self.ref_type = self.ref_type or self.get_ref_type()
        return super(Source, self).save(*args, **kwargs)


class Paper(Document):
    pid = StringField(max_length=23, unique=True, required=True)
    network_collection = StringField()
    pub_year = StringField()

    doi_with_lang = EmbeddedDocumentListField(DOI)

    subject_areas = ListField(StringField())
    paper_titles = EmbeddedDocumentListField(TextAndLang)
    abstracts = EmbeddedDocumentListField(TextAndLang)
    keywords = EmbeddedDocumentListField(TextAndLang)
    references = EmbeddedDocumentListField(Reference)

    recommendations = EmbeddedDocumentListField(Recommendation)
    rejections = EmbeddedDocumentListField(Recommendation)
    linked_by_refs = EmbeddedDocumentListField(Recommendation)

    recommendable = StringField()
    last_proc = DateTimeField()
    proc_status = StringField(choice=RS_PROC_STATUS)

    text_s = StringField()

    # datas deste registro
    created = DateTimeField()
    updated = DateTimeField()

    meta = {
        'collection': 'rs_paper',
        'indexes': [
            'subject_areas',
            'pid',
            'doi_with_lang',
            'pub_year',
            'recommendations',
            'network_collection',
            'recommendable',
            'proc_status',
            {'fields': ['$text_s', ],
             'default_language': 'english',
             'weights': {'text_s': 10, }
            }
        ]
    }

    def clear(self):
        self.network_collection = None
        self.pub_year = None
        self.doi_with_lang = []
        self.subject_areas = []
        self.paper_titles = []
        self.abstracts = []
        self.keywords = []
        self.references = []
        self.recommendations = []
        self.rejections = []
        self.linked_by_refs = []

    def as_dict(self):
        data = {"_id": self._id}
        data.update(paper_summary(self))
        return data

    @property
    def _id(self):
        return str(self.id)

    def get_linked_papers_lists(self, list_names=None, add_uri=None):
        response = {}
        list_names = list_names or ("recommendations", "rejections", "linked_by_refs")
        for list_name in list_names:
            response[list_name] = []
            for item in getattr(self, list_name):
                if add_uri:
                    response[list_name].append(add_uri(item.as_dict()))
                else:
                    response[list_name].append(item.as_dict())
        return response

    def add_linked_paper(self, list_name, linked_paper_id, score=None):
        try:
            paper = Paper.objects(pk=linked_paper_id)[0]
        except IndexError as e:
            print(list_name, linked_paper_id)
            raise e
        if hasattr(self, list_name):
            items = getattr(self, list_name) or []
            items.append(_create_linked_paper(paper, score))
            setattr(self, list_name, items)
            self.last_proc = utcnow()

    def add_doi(self, lang, value, creation_status, registration_status):
        if not self.doi_with_lang:
            self.doi_with_lang = []
        if not all([lang, value]):
            return
        item = DOI()
        item.lang = lang
        item.value = value
        item.creation_status = creation_status
        item.registration_status = registration_status
        self.doi_with_lang.append(item)

    def add_subject_area(self, subject_area):
        if not self.subject_areas:
            self.subject_areas = []
        if not subject_area:
            return
        self.subject_areas.append(subject_area)

    def add_paper_title(self, lang, text):
        if not self.paper_titles:
            self.paper_titles = []
        if not all([lang, text]):
            return
        item = TextAndLang()
        item.lang = lang
        item.text = text
        self.paper_titles.append(item)

    def add_abstract(self, lang, text):
        if not self.abstracts:
            self.abstracts = []
        if not all([lang, text]):
            return
        item = TextAndLang()
        item.lang = lang
        item.text = text
        self.abstracts.append(item)

    def add_keyword(self, lang, text):
        if not self.keywords:
            self.keywords = []
        if not all([lang, text]):
            return
        item = TextAndLang()
        item.lang = lang
        item.text = text
        self.keywords.append(item)

    def add_reference(
        self,
        pub_year,
        vol,
        num,
        suppl,
        page,
        surname,
        organization_author,
        doi,
        journal,
        paper_title,
        source,
        issn,
        thesis_date,
        thesis_loc,
        thesis_country,
        thesis_degree,
        thesis_org,
        conf_date,
        conf_loc,
        conf_country,
        conf_name,
        conf_org,
        publisher_loc,
        publisher_country,
        publisher_name,
        edition,
        source_person_author_surname,
        source_organization_author,
        ):
        if not self.references:
            self.references = []
        item = Reference()
        item.pub_year = pub_year or None
        item.vol = vol or None
        item.num = num or None
        item.suppl = suppl or None
        item.page = page or None
        item.surname = surname or None
        item.organization_author = organization_author or None
        item.doi = doi or None
        item.journal = journal or None
        item.paper_title = paper_title or None
        item.source = source or None
        item.issn = issn or None
        item.thesis_date = thesis_date or None
        item.thesis_loc = thesis_loc or None
        item.thesis_country = thesis_country or None
        item.thesis_degree = thesis_degree or None
        item.thesis_org = thesis_org or None
        item.conf_date = conf_date or None
        item.conf_loc = conf_loc or None
        item.conf_country = conf_country or None
        item.conf_name = conf_name or None
        item.conf_org = conf_org or None
        item.publisher_loc = publisher_loc or None
        item.publisher_country = publisher_country or None
        item.publisher_name = publisher_name or None
        item.edition = edition or None
        item.source_person_author_surname = source_person_author_surname or None
        item.source_organization_author = source_organization_author or None
        self.references.append(item)
        return item

    def save(self, *args, **kwargs):
        if not self.created:
            self.created = utcnow()
        self.updated = utcnow()
        self.text_s = self.text_s or handle_text_s(self)
        return super(Paper, self).save(*args, **kwargs)


class Journal(Document):
    pid = StringField(max_length=9, unique=True, required=True)
    subject_areas = ListField(StringField())
    # datas deste registro
    created = DateTimeField()
    updated = DateTimeField()

    meta = {
        'collection': 'rs_journal',
        'indexes': [
            'subject_areas',
            'pid',
        ]
    }

    def add_subject_area(self, subject_area):
        if not self.subject_areas:
            self.subject_areas = []
        if not subject_area:
            return
        self.subject_areas.append(subject_area)

    def save(self, *args, **kwargs):
        if not self.created:
            self.created = utcnow()
        self.updated = utcnow()

        return super(Journal, self).save(*args, **kwargs)


class CollectionWebsite(Document):
    acron = StringField(required=True)
    names = EmbeddedDocumentListField(TextAndLang)
    url = StringField(required=True)
    # datas deste registro
    created = DateTimeField()
    updated = DateTimeField()

    meta = {
        'collection': 'rs_collection_ws',
        'indexes': [
            'acron',
            'names',
        ]
    }

    def add_name(self, lang, text):
        if not self.names:
            self.names = []
        if not all([lang, text]):
            return
        item = TextAndLang()
        item.lang = lang
        item.text = text
        self.names.append(item)

    def save(self, *args, **kwargs):
        if not self.created:
            self.created = utcnow()
        self.updated = utcnow()

        return super(CollectionWebsite, self).save(*args, **kwargs)


class Hist(Document):
    pid = StringField()
    paper_id = StringField()
    status = StringField(choice=RS_PROC_STATUS)
    created = DateTimeField()
    updated = DateTimeField()

    meta = {
        'collection': 'rs_hist',
        'indexes': [
            'paper_id',
            'pid',
            'status',
            'updated',
        ]
    }

    def save(self, *args, **kwargs):
        if not self.created:
            self.created = utcnow()
        self.updated = utcnow()
        return super(Hist, self).save(*args, **kwargs)
