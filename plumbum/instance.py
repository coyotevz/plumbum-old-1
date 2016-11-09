# -*- coding: utf-8 -*-

"""Plumbum Instance model and related APIs."""

from plumbum.api import IInstanceSetupParticipant, ISystemInfoProvider
from plumbum.core import (
    Component, ComponentManager, ExtensionPoint, implements
)
from plumbum.config import ConfigSection, PathOption, Option, ChoiceOption
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
            for setup_participant in self.setup_participant:
                setup_participant.instance_created()
        else:
            self.verify()
            self.setup_config()
