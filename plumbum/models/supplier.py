# -*- coding: utf-8 -*-

from sqlalchemy.ext.associationproxy import association_proxy
from plumbum.models import db
from plumbum.models.entity import Entity


class Supplier(Entity):
    __tablename__ = 'supplier'
    __mapper_args__ = {'polymorphic_identity': 'supplier'}

    supplier_id = db.Column(db.Integer, db.ForeignKey('entity.id'),
                            primary_key=True)
    name = Entity._name_1
    fancy_name = Entity._name_2

    fiscal_data_id = db.Column(db.Integer, db.ForeignKey('fiscal_data.id'))
    fiscal_data = db.relationship('FiscalData',
                                  backref=db.backref('entity', uselist=False))

    payment_term = db.Column(db.Integer) # in days
    leap_time = db.Column(db.Integer) # in days

    supplier_contacts = db.relationship('SupplierContact',
                                        cascade='all,delete-orphan',
                                        backref='supplier')
    contacts = association_proxy('supplier_contacts', 'contact')

    #: 'products_info' field added by products.ProductSupplierInfo relationship
    #: 'bank_accounts' attribute added by BankAccount.supplier relation
    #: 'purchases' attribute added by PurchaseDocument.supplier relation
    #: 'orders' attribute added by PurchaseOrder.supplier relation

    #: Inherited from Entity
    #:  - address     (collection)
    #:  - phone       (collection)
    #:  - email       (collection)
    #:  - extrafield  (collection)

    def add_contact(self, contact, role):
        self.supplier_contacts.append(SupplierContact(contact, role))

    @property
    def full_name(self):
        fn = " ({0})".format(self.fancy_name) if self.fancy_name else ""
        return "{0}{1}".format(self.name, fn)


class SupplierContact(db.Model):
    __tablename__ = 'supplier_contact'
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.supplier_id'),
                            primary_key=True)
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.contact_id'),
                           primary_key=True)
    role = db.Column(db.Unicode)

    #: 'supplier' attribute is added by Supplier.supplier_contacts relation
    contact = db.relationship('Contact', lazy='joined',
                              backref='supplier_contact')

    def __init__(self, contact, role):
        self.contact = contact
        self.role = role

    def __repr__(self):
        return "<SupplierContact {0}, {1}, {2}>".format(
            self.supplier.name, self.role, self.contact.full_name
        )
