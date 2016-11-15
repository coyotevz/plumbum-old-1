# -*- coding: utf-8 -*-

import imp
import os.path
from glob import glob

from pkg_resources import Environment as PkgEnvironment
from pkg_resources import (DistributionNotFound, UnknownExtra, VersionConflict,
                           working_set)


def _enable_plugin(instance, module):
    """Enable the given plugin module if it wasn't disabled exlicitly."""
    if instance.is_component_enabled(module) is None:
        instance.enable_component(module)


def load_eggs(entry_point_name):
    """Loader that loads any eggs on the search path and `sys.path`."""
    def _load_eggs(instance, search_path, auto_enable=None):
        distributions, errors = working_set.find_plugins(
            PkgEnvironment(search_path)
        )
        for dist in distributions:
            if dist not in working_set:
                instance.log.debug('Adding plugin %s from %s',
                                   dist, dist.location)
                working_set.add(dist)

        def _log_error(item, e):
            se = str(e)
            if isinstance(e, DistributionNotFound):
                instance.log.debug('Skipping "%s": ("%s" not found)', item, se)
            elif isinstance(e, VersionConflict):
                instance.log.error('Skipping "%s": (version conflict "%s")',
                                   item, se)
            elif isinstance(e, UnknownExtra):
                instance.log.error('Skipping "%s": (unknown extra "%s")',
                                   item, se)
            else:
                instance.log.error('Skipping "%s": %s', item, se)

        for dist, e in errors.items():
            _log_error(dist, e)

        for entry in sorted(working_set.iter_entry_points(entry_point_name),
                            key=lambda entry: entry.name):
            instance.log.debug('Loading %s from %s', entry.name,
                               entry.dist.location)
            try:
                entry.load(require=True)
            except Exception as e:
                _log_error(entry, e)
            else:
                if os.path.dirname(entry.dist.location) == auto_enable:
                    _enable_plugin(instance, entry.module_name)

    return _load_eggs


def load_py_files():
    """Loader that look for Python source files in the plugins directories,
    which simply get imported, thereby registering them with the component
    manager if they define any component.
    """
    def _load_py_files(instance, search_path, auto_enable=None):
        for path in search_path:
            plugin_files = glob(os.path.join(path, '*.py'))
            for plugin_file in plugin_files:
                try:
                    plugin_name = os.path.basename(plugin_file[:-3])
                    instance.log.debug('Loading file plugin %s from %s',
                                       plugin_name, plugin_file)
                    if plugin_name not in sys.modules:
                        module = imp.load_source(plugin_name, plugin_file)
                    if path == auto_enable:
                        _enable_plugin(instance, plugin_name)
                except Exception as e:
                    instance.log.error('Failed to load plugin from %s: %s',
                                       plugin_file, e)

    return _load_py_files


def load_components(instance, extra_path=None,
                   loaders=(load_eggs('plumbum.plugins'), load_py_files())):
    """Load all plugins components found on the given search path."""
    plugins_dir = instance.plugins_dir
    search_path = [plugins_dir]
    if extra_path:
        search_path = list(extra_path)

    for loadfunc in loaders:
        loadfunc(instance, search_path, auto_enable=plugins_dir)
