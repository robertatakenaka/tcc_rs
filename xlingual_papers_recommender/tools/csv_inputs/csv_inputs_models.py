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

    def save(self, *args, **kwargs):
        if not self.created:
            self.created = utcnow()
        self.updated = utcnow()
        return super(CSVRow, self).save(*args, **kwargs)
