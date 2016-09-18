# -*- coding: utf-8 -*-

from plumbum.models import db


class ProductSupplierInfo(db.Model):
    """Supplier information for a |product|.

    Each product can has more than one |supplier|.
    """
    __tablename__ = 'product_supplier_info'


class ProductCategory(db.Model):
    __tablename__ = 'product_category'


class Product(db.Model):
    """A Product is a thing that can be:

    * ordered (via |purchase|)
    * stored (via |storable|)
    * sold (via |sellable|)

    If the product does not use stock management, it will be possible to sell
    items, even if it was never purchased.
    """
    __tablename__ = 'product'

    #: the product is availbale and can be used on  |purchase|/|sale|
    STATUS_AVAILABLE = 'STATUS_AVAILABLE'

    #: the  product is closed, that is, ti still exists for references
    #: but it should not be posible to create a |purchase|/|sale| with it
    STATUS_CLOSED = 'STATUS_CLOSED'

    #: the product is suspended, that is, it still exists for future references but it should no be possile to create |purchase|/|sale| with it
    STATUS_SUSPENDED = 'STATUS_SUSPENDED'


class ProductHistory(db.Model):
    """Class that track product changes in time, like price, supplier, price
    configuration, cost configuration, etc.
    """
    __tablename__ = 'product_history'


class ProductStockItem(db.Model):
    """Class that makes a reference to the |product| stock of a certain
    |branch|.
    """
    __tablename__ = 'product_stock_item'


class Storable(db.Model):
    """Storable represents the stock information of a |product|, like minimum,
    maximum, reorder point, etc.

    The actual stock of an item is in ProductStockItem.
    """
    pass


class StockTransactionHistory(db.Model):
    """This class stores information about all transactions made in the stock

    Everytime a |storable| has its stock increased or decreased, an object of
    this class will be created, registering the quantity, cost, responsible and
    reason for the transaction.
    """
    pass
