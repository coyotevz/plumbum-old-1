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


class IInstanceSetupParticipant(Interface):
    """Extension point interface for components that need to participate in the
    creation and upgrading of Plumbum instances, for example to create
    additional database tables.

    Please note the `IInstanceSetupParticipant` instances are called in
    arbitrary order. If your upgrades must be ordered consistently, please
    implement the ordering in a single `IInstanceSetupParticipant`. See the
    database upgrade infraestructure in Plumbum core for an example.
    """

    def instance_created():
        """Called when a new Plumbum instance is created."""

    def instance_needs_upgrade():
        """Called when Plumbum checks whether the instance needs to be
        upgraded.

        Should return `True` if the participant needs an upgrade to be
        performed, `False` otherwhise.
        """

    def upgrade_instance():
        """Actually perform an instance upgrade.

        Implementations of this method don't need to commit any database
        transaction. This is done implicitly for each participant if the
        upgrade succeeds without an error being raised.

        However, if the `upgrade_instance` consist of small, restartable,
        steps of upgrade, it can decide to commit on its own after each
        successful step.
        """
