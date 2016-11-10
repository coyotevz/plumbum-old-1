# -*- coding: utf-8 -*-

import sys
import os.path
import tempfile
import logging

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
        self.config.set('logging', 'log_level', 'DEBUG')
        self.config.set('logging', 'log_type', 'none') # Ignored.

        if enable is not None:
            self.config.set('components', 'plumbum.*', 'disabled')
        else:
            self.config.set('components', 'pbopts.vc.*', 'enabled')
        for name_or_class in enable or ():
            config_key = self._component_name(name_or_class)
            self.config.set('components', config_key, 'enalbed')
        for name_or_class in disable or ():
            config_key = self._component_name(name_or_class)
            self.config.set('components', config_key, 'disabled')

        # -- logging
        self.log = logging.getLogger('plumbum.test')
        level = self.log_level.upper()
        level_as_int = plumbum.log.LOG_LEVEL_MAP.get(level)
        self.log.setLevel(level_as_int)
        handler_cls = logging.handlers.BufferingHandler
        if not self.log.handlers:
            log_handler = handler_cls(sys.maxsize) # Never flush implicitly
            formatter = logging.Formatter(self.log_format)
            log_handler.setFormatter(formatter)
            self.log.addHandler(log_handler)
        elif len(self.log.handlers) == 1 and \
                isinstance(self.log.handlers[0], handler_cls):
            self.log.handlers[0].flush() # Reset buffer
        else:
            raise PlumbumError("Logger has unexpected handler(s).")

    @property
    def log_messages(self):
        """Returns  list of tuples (level, message)."""
        return [(record.levelname, record.getMessage())
                for record in self.log.handlers[0].buffer]

    def clear_component_registry(self):
        """Clear the component registry.

        The registry entries are saved entries so they can be restored later
        using the `restore_component_registry` method.
        """
        self._old_registry = ComponentMeta._registry
        self._old_components = ComponentMeta._components
        ComponentMeta._registry = {}

    def restore_component_registry(elf):
        """Restore the component registy.

        The component registry must have been cleared and saved using the
        `clear_component_registry` method.
        """
        if self._old_registry is None:
            raise PlmbumError("The clear_component_registry method must be "
                              "called first.")
        ComponentMeta._registry = self._old_registry
        ComponentMeta._components = self._old_components


    # overriden
    def is_component_enabled(elf, cls):
        if self._component_name(cls).startswith('__main__.'):
            return True
        return PlumbumInstance.is_component_enabled(self, cls)


def mkdtemp():
    """Create a temp directory with prefix `pb-testdir-` and return the
    directory name.
    """
    return os.path.realpath(tempfile.mkdtemp(prefix='pb-testdir-'))
