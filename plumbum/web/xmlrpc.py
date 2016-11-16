# -*- coding: utf-8 -*-

from xmlrpc.server import SimpleXMLRPCDispatcher

from plumbum.core import Component, implements
from plumbum.api import IRoutesProvider
from plumbum.config import Option


_dispatcher = SimpleXMLRPCDispatcher(allow_none=False, encoding=None)


class XMLRPCService(Component):

    implements(IRoutesProvider)

    ## IRoutesProvider methods

    def add_routes(self, routes):
        base_url = self.xmlrpc_base_url
        if not base_url.startswith('/'):
            base_url = '/' + base_url
        routes.add_url(base_url, endpoint='plumbum/xmlrpc', view=self.xmlrpc_handler)
