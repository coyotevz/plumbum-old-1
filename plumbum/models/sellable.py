# -*- coding: utf-8 -*-

from plumbum.models import db


class SellableUnit(db.Model):
    """The unit of a |sellable|.
    When selling a sellable in a |sale| the quantity of a |saleitem| will be
    entered in this unit.
    """
    pass


class SellableTaxConstant(db.Model):
    """A tax constant tied to a sellable."""
    pass


class SellableCategory(db.Model):
    """A sellable category.

    A way to group several |sellables| together.

    A category can define markup, tax and comission, the values of the category
    will only be used when the sellable itself lacks a value.

    Sellable categories can be grouped recursively.
    """
    pass


class Sellable(db.Model):
    """Sellable information of certain item such a |product| or a |service|.
    """
    pass
