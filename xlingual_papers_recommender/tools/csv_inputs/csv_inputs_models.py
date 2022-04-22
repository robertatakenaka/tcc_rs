from xlingual_papers_recommender import exceptions

from datetime import datetime

from mongoengine import (
    Document,
    StringField,
    DateTimeField,
    DictField,
)


def utcnow():
    return datetime.utcnow()


class CSVRow(Document):
    pid = StringField()
    lang = StringField()
    name = StringField()
    data = DictField()

    # datas deste registro
    created = DateTimeField()
    updated = DateTimeField()

    meta = {
        'collection': 'csv_row',
        'indexes': [
            'pid',
            'lang',
            'name',
        ]
    }

    def as_dict(self):
        return dict(
            pid=self.pid,
            lang=self.lang,
            name=self.name,
            data=self.data,
        )

    def save(self, *args, **kwargs):
        if not self.created:
            self.created = utcnow()
        self.updated = utcnow()
        return super(CSVRow, self).save(*args, **kwargs)


class PaperJSON(Document):
    pid = StringField()
    data = DictField()
    original_pid = StringField()

    # datas deste registro
    created = DateTimeField()
    updated = DateTimeField()

    meta = {
        'collection': 'paper_as_json',
        'indexes': [
            'pid',
            'original_pid',
        ]
    }

    def as_dict(self):
        return dict(
            pid=self.pid,
            data=self.data,
            original_pid=self.original_pid,
        )

    def save(self, *args, **kwargs):
        if not self.created:
            self.created = utcnow()
        self.updated = utcnow()
        return super(PaperJSON, self).save(*args, **kwargs)
