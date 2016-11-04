# -*- coding: utf-8 -*-

from plumbum.core import Interface

class ISystemInfoProvider(Interface):
    """Provider of system information, displayed in the "About Plumbum" page
    and in internal error reports.
    """
    def get_system_info():
        """Yield a sequence of `(name, version)` tuples describing the name and
        version information of external packages used by a component.
        """


class IEnvironmentSetupParticipant(Interface):
    """Extension point interface for components that need to participate in the
    creation and upgrading of Plumbum environments, for example to create
    additional database tables.

    Please note the `IEnvironmentSetupParticipant` instances are called in
    arbitrary order. If your upgrades must be ordered consistently, please
    implement the ordering in a single `IEnvironmentSetupParticipant`. See the
    database upgrade infraestructure in Plumbum core for an example.
    """

    def environment_created():
        """Called when a new Plumbum environment is created."""

    def environment_needs_upgrade():
        """Called when Plumbum checks whether the environment needs to be
        upgraded.

        Should return `True` if the participant needs an upgrade to be
        performed, `False` otherwhise.
        """

    def upgrade_environment():
        """Actually perform an environment upgrade.

        Implementations of this method don't need to commit any database
        transaction. This is done implicitly for each participant if the
        upgrade succeeds without an error being raised.

        However, if the `upgrade_environment` consist of small, restartable,
        steps of upgrade, it can decide to commit on its own after each
        successful step.
        """
