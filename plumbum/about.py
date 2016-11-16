# -*- coding: utf-8 -*-

from plumbum.core import Component, implements


class AboutModule(Component):
    """About Plumbum provider, showing version information from third-party
    packages, as sell as configuration information.
    """
    required = True
