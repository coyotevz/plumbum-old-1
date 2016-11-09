# -*- coding: utf-8 -*-

import os.path

from plumbum.core import ComponentManager
from plumbum.config import Configuration
from plumbum.instance import PlumbumInstance


class InstanceStub(PlumbumInstance):
    """A stub of the plumbum.instance.Instance class for testing."""

    required = False
    abstract = True

    def __init__(self, default_data=False, enable=None, disable=None,
                 path=None, destroying=False):
        """Construct a new Instance stub object.

        :param default_data: If True, populate the database with some defaults.
        :param enable: A list of components classes or name globs to activate
                       in the stub instance.
        :param disable: A list of component classes or name globs to deactivate
                        in the stub instance.
        :param path: The location of the instance in the file system. No
                     files or directories are created when specifying this
                     parameter.
        :param destroying: If True, the database will not be reset. This is
                           useful for cases when the object is being
                           constructed in order to call `destroy_db`.
        """
        if enable is not None and not isinstance(enable, (list, tuple)):
            raise TypeError('Keyword argument "enable" must be a list')
        if disable is not None and not isinstance(disable, (list, tuple)):
            raise TypeError('Keyword argument "disable" must be a list')

        ComponentManager.__init__(self)

        self._old_registry = None
        self._old_components = None

        import plumbum
        self.path = path
        if self.path is None:
            self.path = os.path.abspath(os.path.dirname(plumbum.__file__))
        self.path = os.path.normpath(os.path.normcase(self.path))

        # -- configuration
        self.config = Configuration(None)
