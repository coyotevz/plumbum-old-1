# -*- coding: utf-8 -*-

from datetime import datetime
from sqlalchemy.ext.declarative import declared_attr
from plumbum.models import db


class TimestampMixin(object):

    created = db.Column(db.DateTime, default=datetime.now)
    modified = db.Column(db.DateTime, default=datetime.now,
                         onupdate=datetime.now)

    @staticmethod
    def stamp_modified(mapper, connection, target):
        if db.object_session(target).is_modified(target):
            target.modified = datetime.now()

    @classmethod
    def __declare_last__(cls):
        db.event.listen(cls, 'before_update', cls.stamp_modified)


class RefEntityMixin(object):

    @declared_attr
    def entity_id(cls):
        return db.Column('entity_id', db.Integer, db.ForeignKey('entity.id'),
                         nullable=False)

    @declared_attr
    def entity(cls):
        name = cls.__name__.lower()
        return db.relationship('Entity',
                               backref=db.backref(name, lazy='joined'),
                               lazy='joined')


class Address(RefEntityMixin, db.Model):
    """Stores addresses information"""
    __tablename__ = 'address'

    id = db.Column(db.Integer, primary_key=True)
    address_type = db.Column(db.Unicode)
    street = db.Column(db.Unicode(128), nullable=False)
    city = db.Column(db.Unicode(64))
    province = db.Column(db.Unicode(32), nullable=False)
    postal_code = db.Column(db.Unicode(32))

    def __str__(self):
        retval = self.street
        if self.city:
            retval += ", {}".format(self.city)
        retval += ", {}".format(self.province)
        if self.postal_code:
            retval += " ({})".format(self.postal_code)
        return retval

    def __repr__(self):
        return "<Address '{}' of '{}: {}'>".format(
            str(self),
            self.entity.entity_type,
            self.entity.full_name
        )


class Phone(RefEntityMixin, db.Model):
    """Model to store phone information"""
    __tablename__ = 'phone'

    id = db.Column(db.Integer, primary_key=True)
    phone_type = db.Column(db.Unicode)
    prefix = db.Column(db.Unicode(8))
    number = db.Column(db.Unicode, nullable=False)
    extension = db.Column(db.Unicode(5))

    def __str__(self):
        retval = self.phone_type + ': ' if self.phone_type else ''
        if self.prefix:
            retval += "({})".format(self.prefix)
        retval += self.number
        if self.extension:
            retval += " ext: {}".format(self.extension)
        return retval

    def __repr__(self):
        return "<Phone '{}' of '{}: {}'>".format(
            str(self),
            self.entity.entity_type,
            self.entity.full_name
        )


class Email(RefEntityMixin, db.Model):
    """Model to store email information"""
    __tablename__ = 'email'

    id = db.Column(db.Integer, primary_key=True)
    email_type = db.Column(db.Unicode(50))
    email = db.Column(db.Unicode(50), nullable=False)

    def __str__(self):
        retval = self.email_type + ': ' if self.email_type else ''
        retval += self.email
        return retval

    def __repr__(self):
        return "<Email '{}' of '{}: {}'>".format(
            str(self),
            self.entity.entity_type,
            self.entity.full_name
        )


class ExtraField(RefEntityMixin, db.Model):
    """Model to store information of additional data"""
    __tablename__ = 'extra_field'

    id = db.Column(db.Integer, primary_key=True)
    field_name = db.Column(db.Unicode(50), nullable=False)
    field_value = db.Column(db.Unicode(50), nullable=False)

    def __str__(self):
        return self.field_name + ': ' + self.field_value

    def __repr__(self):
        return "<ExtraField '{}' of '{}: {}'>".format(
            self(str),
            self.entity.entity_type,
            self.entity.full_name
        )
