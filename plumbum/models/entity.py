# -*- coding: utf-8 -*-

from plumbum.models import db
from plumbum.models.misc import TimestampMixin


class Entity(db.Model, TimestampMixin):
    """
    Base class for entity submodels.

    An entity is a model that has two names, one required and one optional, and
    a series of address, phones, emails and extra fields.
    Models to be suitable to this description are for example: User, Employee,
    Supplier, Customer, Contact, Branch, etc.
    """
    __tablename__ = 'entity'

    id = db.Column(db.Integer, primary_key=True)
    _name_1 = db.Column('name_1', db.Unicode, nullable=False)
    _name_2 = db.Column('name_2', db.Unicode)
    entity_type = db.Column(db.Unicode(50))
    notes = db.Column(db.UnicodeText)
    __mapper_args__ = {'polymorphic_on': entity_type}

    @property
    def full_name(self):
        ln = " {0}".format(self._name_2) if self._name_2 else ""
        return "{0}{1}".format(self._name_1, ln)

    def __repr__(self):
        return "<{0} '{1}'>".format(self.__class__.__name__,
                                    self.full_name)
