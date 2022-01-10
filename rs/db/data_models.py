from datetime import datetime

from mongoengine import (
    EmbeddedDocument,
    EmbeddedDocumentListField,
    Document,
    StringField,
    DictField,
    ListField,
    DateField,
    DateTimeField,
    DecimalField,
)

DOI_CREATION_STATUS = ('auto_assigned', 'assigned_by_editor', 'UNK')
DOI_REGISTRATION_STATUS = ('registered', 'not_registered', 'UNK')
ISSN_TYPES = ('epub', 'ppub', 'l', 'scielo-id')


def utcnow():
    return datetime.utcnow() #.isoformat().replace("T", " ") + "Z"


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
        return {
            "pid": self.pid,
            "network_collection": self.network_collection,
            "pub_year": self.pub_year,
            "doi_with_lang": self.doi_with_lang,
            "paper_titles": self.paper_titles,
            "abstracts": self.abstracts,
        }

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
        ]
    }

    def add_referenced_by(self, paper_id):
        str_paper_id = str(paper_id)
        if not self.referenced_by:
            self.referenced_by = []
        if str_paper_id not in self.referenced_by:
            self.referenced_by.append(str_paper_id)

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

    def save(self, *args, **kwargs):
        if not self.created:
            self.created = utcnow()
        self.updated = utcnow()
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
            '$paper_titles__text',
            '$abstracts__text',
            '$keywords__text',
        ]
    }

    @property
    def _id(self):
        return str(self.id)

    def add_recommendation(self, pid, network_collection, pub_year, doi_with_lang, paper_titles, abstracts, score):
        if not self.recommendations:
            self.recommendations = []
        item = Recommendation()
        item.pid = pid
        item.network_collection = network_collection
        item.pub_year = pub_year
        item.doi_with_lang = doi_with_lang
        item.paper_titles = paper_titles
        item.abstracts = abstracts
        item.score = score
        self.recommendations.append(item)

    def add_rejection(self, pid, network_collection, pub_year, doi_with_lang, paper_titles, abstracts, score):
        if not self.rejections:
            self.rejections = []
        item = Recommendation()
        item.pid = pid
        item.network_collection = network_collection
        item.pub_year = pub_year
        item.doi_with_lang = doi_with_lang
        item.paper_titles = paper_titles
        item.abstracts = abstracts
        item.score = score
        self.rejections.append(item)

    def add_linked_by_refs(self, pid, network_collection, pub_year, doi_with_lang, paper_titles, abstracts):
        if not self.linked_by_refs:
            self.linked_by_refs = []
        item = Recommendation()
        item.pid = pid
        item.network_collection = network_collection
        item.pub_year = pub_year
        item.doi_with_lang = doi_with_lang
        item.paper_titles = paper_titles
        item.abstracts = abstracts
        self.linked_by_refs.append(item)

    def add_doi(self, lang, value, creation_status, registration_status):
        if not self.doi_with_lang:
            self.doi_with_lang = []
        if not all([lang, value]):
            return
        item = DOI()
        item.type = type
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
