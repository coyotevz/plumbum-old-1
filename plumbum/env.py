# -*- coding: utf-8 -*-

"""Plumbum Environment model and related APIs."""

from plumbum.api import IEnvironmentSetupParticipant, ISystemInfoProvider
from plumbum.core import (
    Component, ComponentManager, ExtensionPoint, implements
)
from plumbum.config import ConfigSection


# Content of the VERSION file in the environment
_VERSION = 'Plumbum Environment Version 1'


class Environment(Component, ComponentManager):
    """Plumbum environment manager.

    Plumbum sotres project information in a Plumbum environment. It consists of
    a directory structure containing among other things:

    * a configuration file,
    * project-specific templates and plugins,
    * the SQLite database file in case the database backend is sqlite
    """

    implements(ISystemInfoProvider)

    required = True

    system_info_providers = ExtensionPoint(ISystemInfoProvider)
    setup_participants = ExtensionPoint(IEnvironmentSetupParticipant)

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
        [Components]
        pb.ticket.report.ReportModule = disabled
        acct_mgr.* = enabled
        }}}

        This first option tells Plumbum to disable the [wiki:TracReports report
        module]. The second option instruct Plumbum to enable all components in
        the `acct_mgr` package. Note that the trailing willcard is required for
        module/package matching.

        To view the list of active components, go to the ''Plugins'' page on
        ''About Plumbum'' (requires `CONFIG_VIEW` [wiki:PlumbumPermissions
        permissions]).

        See also: PlumbumPlugins
        """)

    shared_plugins_dir = PathOption('inherit', 'plugins_dir', '',
        """Path to the //shared plugins directory//.

        Plugins in that directory are loaded in addition to thouse in the directory of the environment `plugins`, with this one taking precedence.
        """)

    base_url = Option('plumbum', 'base_url', '',
        """Reference URL for the Plumbum deployment.

        This is the base URL that will be used when producing documents that
        will be used outside of the web browsing context, like for example when
        inserting URLs pointing to Plumbum resources in notification
        e-mails.""")

    def __init__(self, path, create=False, options=[]):
        """Initialize the Plumbum environment.

        :param path:   the absolute path to the Plumbum environment
        :param create: if `True`, the environment is created and populated with
                       default data; otherwise, the environment is expected to
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
                setup_participant.environment_created()
        else:
            self.verify()
            self.setup_config()
