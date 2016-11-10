# -*- coding: utf-8 -*-

"""Plumbum Instance model and related APIs."""

import os
import hashlib

from plumbum.api import IInstanceSetupParticipant, ISystemInfoProvider
from plumbum.core import (
    Component, ComponentManager, ExtensionPoint, implements, PlumbumError
)
from plumbum.config import (
    ConfigSection, PathOption, Option, ChoiceOption,
    Configuration, ConfigurationError
)
from plumbum.util import lazy, as_bool
from plumbum.util.file import create_file
from plumbum import log


# Content of the VERSION file in the instance
_VERSION = 'Plumbum Instance Version 1'


class PlumbumInstance(Component, ComponentManager):
    """Plumbum instance manager.

    Plumbum stores instance information in a PlumbumInstance. It consists of
    a directory structure containing among other things:

    * a configuration file,
    * instance-specific templates and plugins,
    * the SQLite database file in case the database backend is sqlite
    """

    implements(ISystemInfoProvider)

    required = True

    system_info_providers = ExtensionPoint(ISystemInfoProvider)
    setup_participants = ExtensionPoint(IInstanceSetupParticipant)

    components_section = ConfigSection('components',
        """This section is used to enable or disable components provided by
        plugins, as well as by Plumbum itself. The component to enable/disable
        is specified via the name of the option. Whether its enalbed is
        determined by the option value; setting the value to `enabled` or `on`
        will enable the component, any other value (typically `disabled` or
        `off`) will disable the component.

        The option name is either the fully qualified name of the components or
        the module/package prefix of the component. The former enabled/disables
        a specific component, while the latter enables/disables any component
        in the specified package/module.

        Consider the following configuration snippet:
        {{{
        [components]
        pb.report.ReportModule = disabled
        acct_mgr.* = enabled
        }}}

        This first option tells Plumbum to disable the report module. The
        second option instruct Plumbum to enable all components in the
        `acct_mgr` package. Note that the trailing willcard is required for
        module/package matching.

        To view the list of active components, go to the ''Plugins'' page on
        ''About Plumbum'' (requires `CONFIG_VIEW` [wiki:PlumbumPermissions
        permissions]).

        See also: PlumbumPlugins
        """)

    shared_plugins_dir = PathOption('inherit', 'plugins_dir', '',
        """Path to the //shared plugins directory//.

        Plugins in that directory are loaded in addition to those in the
        directory of the instance `plugins`, with this one taking precedence.
        """)

    #base_url = Option('plumbum', 'base_url', '',
    #    """Reference URL for the Plumbum deployment.

    #    This is the base URL that will be used when producing documents that
    #    will be used outside of the web browsing context, like for example when
    #    inserting URLs pointing to Plumbum resources in notification
    #    e-mails.""")

    instance_name = Option('instance', 'name', 'My Store',
        """Name of the instance.""")

    instance_description = Option('instance', 'descr', 'My example store',
        """Short description of the instance.""")

    instance_admin = Option('instance', 'admin', '',
        """E-mail address of the instance's administrator.""")

    log_type = ChoiceOption('logging', 'log_type',
                            log.LOG_TYPES + log.LOG_TYPE_ALIASES,
        """Logging facility to use.

        Should be one of (`none`, `file`, `stderr`, `syslog`, `winlog`).""")

    log_file = Option('logging', 'log_file', 'plumbum.log',
        """If `log_type` is `file`, this should be a path to the log-file.
        Relative paths are resolved relative to the `log` directory of the
        instance.""")

    log_level = ChoiceOption('logging', 'log_level',
                             tuple(reversed(log.LOG_LEVELS)) +
                             log.LOG_LEVEL_ALIASES,
        """Level of verbosity in log.

        Should be one of (`CRITICAL`, `ERROR`, `WARNING`, `INFO`, `DEBUG`).""")

    log_format = Option('logging', 'log_format', None,
        """Custom logging format.

        If nothing is set, the folowing will be used:

        `Plumbum[$(module)s] $(levelname)s: $(message)s`

        In addition to regular key names supported by the
        [http://docs.python.org/library/logging.html Python logger library]
        one could use:

        - `$(path)s`      the path for the current instance
        - `$(basename)s`  the last path component of the current instance
        - `$(instance)s`  the instance name

        Note the usage of `$(...)s` instead of `%(...)s` s the latter form
        would be interpreded by the !ConfigParser itself.

        Example:
        `($(thread)d) PB[$(basename)s:$(module)s] $(levelname)s: $(message)s`
        """)

    def __init__(self, path, create=False, options=[]):
        """Initialize the Plumbum instance.

        :param path:   the absolute path to the Plumbum instance
        :param create: if `True`, the instance is created and populated with
                       default data; otherwise, the instance is expected to
                       already exists.
        :param options: A list of `(section, name, value)` tuples that define
                       configuration options
        """
        ComponentManager.__init__(self)

        self.path = os.path.normpath(os.path.normcase(path))
        self.log = None
        self.config = None

        if create:
            self.create(options)
            for setup_participant in self.setup_participants:
                setup_participant.instance_created()
        else:
            self.verify()
            self.setup_config()

    @lazy
    def name(self):
        """The instance name."""
        return os.path.basename(self.path)

    @property
    def instance(self):
        """Property returning the `Instance` object, which is often required
        for functions and methods that take a `Component` instance."""
        return self

    @property
    def system_info(self):
        """List of `(name, version)` tuple describing the name and version
        information of external packages used by Plumbum and plugins."""
        info = []
        for provider in self.system_info_providers:
            info.extend(provider.get_system_info() or [])
        return sorted(set(info),
                      key=lambda name, ver: (name != 'Plumbum', name.lower())
               )

    # ISystemInfoProvider methods

    def get_system_info(self):
        yield 'Plumbum', self.plumbum_version
        yield 'Python', sys.version
        yield 'setuptools', setuptools.__version__
        if pytz is not None:
            yield 'pytz', pytz.__version__
        if hasattr(self, 'webfrontend_version'):
            yield self.webfrontend, self.webfrontend_version

    def component_activated(self, component):
        """Initialize additional member variables for components.

        Every component activated through the `Instance` object gets three
        member variabled: `instance` (the instance object), `config` (the
        instance configuration) and `log` (a logger object)."""
        component.instance = self
        component.config = self.config
        component.log = self.log

    def _component_name(self, name_or_class):
        name = name_or_class
        if not isinstance(name_or_class, str):
            name = name_or_class.__module__ + '.' + name_or_class.__name__
        return name.lower()

    @lazy
    def _component_rules(self):
        _rules = {}
        for name, value in self.components_section.options():
            name = name.rstrip('.*').lower()
            _rules[name] = as_bool(value)
        return _rules

    def is_component_enabled(self, cls):
        """Implemented to only allow activation of components that are not
        disabled in the configuration.

        This is called by the `ComponentManager` base class when a component is
        about to be activated. If this method returns `False`, the component
        does not get activated. If it returns `None`, the component only gets
        activated if it is located in the `plugins` directory of the instance.
        """
        component_name = self._component_name(cls)

        rules = self._component_rules
        cname = component_name
        while cname:
            enabled = rules.get(cname)
            if enabled is not None:
                return enabled
            idx = cname.rfind('.')
            if idx < 0:
                break
            cname = cname[:idx]

        # By default, all components in the plumbum package are enabled except
        # tests
        return component_name.startswith('plumbum.') and \
                not component_name.startswith('plumbum.test.') and \
                not component_name.startswith('plumbum.tests.') or None

    def enable_component(self, cls):
        """Enable a component or module."""
        self._component_rules[self._component_name(cls)] = True
        super(PlumbumInstance, self).enable_component(cls)

    def verify(self):
        """Verify that the provided path points to a valid Plumbum instance
        directory."""
        try:
            tag = read_file(os.path.join(self.path, 'VERSION')).splitlines()[0]
            if tag != _VERSION:
                raise Exception("Unknown Plumbum instance type '%(type)s'" %\
                                dict(type=tag))
        except Exception as e:
            raise PlumbumError("No Plumbum instance found at %(path)s\n"
                               "%(e)s" % dict(path=self.path, e=e))

    def shutdown(self, tid=None):
        """Close the instance."""
        # Must shutdown database manager, etc.
        if tid is None:
            log.shutdown(self.log)

    def create(self, options=[]):
        """Create the basic directory structure of the instance, initialize the
        database and populate the configuration file with default values.

        If options contains ('inherit', 'file'), default values will not be
        loaded; they are expected to be provided by that file or other
        options.
        """
        # Create the directory structure
        if not os.path.exists(self.path):
            os.mkdir(self.path)
        os.mkdir(self.log_dir)
        #os.mkdir(self.htdocs_dir)
        os.mkdir(self.plugins_dir)

        # Create a few files
        create_file(os.path.join(self.path, 'VERSION'), _VERSION + '\n')
        create_file(os.path.join(self.path, 'README'),
                "This directory contains a Plumbum instance.\n"
                "Visit http://pb.rioplomo.com/ for more information.\n")

        # Setup the default configuration
        os.mkdir(self.conf_dir)
        create_file(self.config_file_path + '.sample')
        config = Configuration(self.config_file_path)
        for section, name, value in options:
            config.set(section, name, value)
        config.save()
        self.setup_config()
        if not any((section, option) == ('inherit', 'file')
                   for section, option, value in options):
            self.config.set_defaults(self)
            self.config.save()

        # Create the database

    @lazy
    def database_version(self):
        """Returns the current version of the database."""
        return False

    @lazy
    def plumbum_version(self):
        """Returns the version of Plumbum."""
        return '0.0-dev'

    def setup_config(self):
        """Load the configuration file."""
        self.config = Configuration(self.config_file_path,
                                    {'instname': self.name})
        if not self.config.exists:
            raise PlumbumError("The configuration file is not found at "
                               "%(path)s" % dict(path=self.config_file_path))
        self.setup_log()
        #plugins_dir = self.shared_plugins_dir
        #load_components(self, plugins_dir and (plugins_dir,))

    @lazy
    def config_file_path(self):
        """Path of the plumbum.ini file."""
        return os.path.join(self.conf_dir, 'plumbum.ini')

    @lazy
    def log_file_path(self):
        """Path to the log file."""
        if not os.path.isabs(self.log_file):
            return os.path.join(self.log_dir, self.log_file)
        return self.log_file

    def _build_path(self, *dirs):
        path = self.path
        for dir in dirs:
            path = os.path.join(path, dir)
        return os.path.realpath(path)

    @lazy
    def conf_dir(self):
        """Absolute path to the conf directory."""
        return self._build_path('conf')

    @lazy
    def log_dir(self):
        """Absolute path to the log directory."""
        return self._build_path('log')

    @lazy
    def plugins_dir(self):
        """Absolute path to the plugins directory."""
        return self._build_path('plugins')

    @lazy
    def templates_dir(self):
        """Absolute path to the templates directory."""
        return self._build_path('templates')

    def setup_log(self):
        """Initialize the logging sub-system."""
        format = self.log_format
        if format:
            format = format.replace('$(', '%(') \
                           .replace('%(path)s', self.path) \
                           .replace('%(basename)s', self.name) \
                           .replace('%(name)s', self.instance_name)
        logid = 'Plumbum.%s' % hashlib.sha1(self.path.encode('utf-8')).hexdigest()
        self.log = log.logger_handler_factory(
            self.log_type, self.log_file_path, self.log_level, logid,
            format=format)
        self.log.info('-' * 32 + ' instance startup [Plumbum %s] ' + '-' * 32,
                      self.plumbum_version)

    def needs_upgrade(self):
        """Return whether the instance needs to be upgraded."""
        for participant in self.setup_participants:
            if participant.instance_needs_upgrade():
                self.log.warn("Component %s requires instance upgrade" %\
                              participant)
                return True
        return False

    def upgrade(self, backup=False, backup_dest=None):
        """Upgrade instance."""
        upgraders = []
        for participant in self.setup_participants:
            if participant.instance_needs_upgrade():
                upgraders.append(participant)
        if not upgraders:
            return

        for participant in upgraders:
            self.log.info("%s.%s upgrading..." % (participant.__module__,
                          participant.__class__.__name__))
            participant.upgrade_instance()
            # TODO: upgrade database
        return True


class PlumbumInstanceSetup(Component):
    """Manage automatic instance upgrades."""

    required = True

    implements(IInstanceSetupParticipant)

    # IInstanceSetupParticipant methods

    def instance_created(self):
        """Insert default data into the dataabse."""
        # TODO: insert default data to db
        self._update_sample_config()

    def instance_needs_upgrade(self):
        # TODO: Check if db needs upgrade
        return False

    def upgrade_instance(self):
        # TODO: upgrade db
        self._update_sample_config()

    # Internal methods

    def _update_sample_config(self):
        filename = os.path.join(self.instance.config_file_path + '.sample')
        if not os.path.isfile(filename):
            return
        config = Configuration(filename)
        for (section, name), option in Option.get_registry().items():
            config.set(section, name, option.dumps(option.default))
        try:
            config.save()
            self.log.info("Wrote sample configuration file with the new "
                          "settings and their default values: %s" % filename)
        except IOError as e:
            self.log.warn("Could't write sample configuration file (%s)", e,
                          exc_info=True)
