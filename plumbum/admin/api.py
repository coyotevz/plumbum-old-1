# -*- coding: utf-8 -*-

import os

from plumbum.core import Component, ExtensionPoint, Interface, PlumbumError

LANG = os.environ.get('LANG')

console_date_format = '%Y-%m-%d'
console_datetime_format = '%Y-%m-%d %H:%M:%S'
console_date_format_hint = 'YYYY-MM-DD'


class AdminCommandError(PlumbumError):
    """Exception raised when an admin command cannot be executed."""
    
    def __init__(self, msg, show_usage=False, cmd=None):
        PlumbumError.__init__(self, msg)
        self.show_usage = show_usage
        self.cmd = cmd


class IAdminCommandProvider(Interface):
    """Extension point interface for adding commands to the console
    administration interface `plumbum-admin`.
    """

    def get_admin_commands():
        """Return a list of available admin commands.

        The items returned by this funciton must be tuples of the form
        `(command, args, help, complete, execute)`, where `command`contains the
        space-separated command and sub-command names, `args` is a string
        describing the command arguments and `help` is the help text. The first
        paragraph of the help text is taken as a short help, shown in the list
        of commands.

        `complete` is called to auto-complete the command arguments, with the
        current list of arguments as its only argument. It should return a list
        of relevant values for the last argument in the list.

        `execute` is called to execute the command, with the command arguments
        passed as positional arguments.
        """


class AdminCommandManager(Component):
    """plumbum-admin command manager."""

    providers = ExtensionPoint(IAdminCommandProvider)

    def get_command_help(self, args=[]):
        """Return help information for a set of commands."""
        commands = []
        for provider in self.providers:
            for cmd in provider.get_admin_commands() or []:
                parts = cmd[0].split()
                if parts[:len(args)] == args:
                    commands.append(cmd[:3])
        commands.sort()
        return commands

    def complete_command(self, args, cmd_only=False):
        """Perform auto-completion on the given arguments."""
        comp = []
        for provider in self.providers:
            for cmd in provider.get_admin_commands() or []:
                parts = cmd[0].split()
                plen = min(len(parts), len(args) - 1)
                if args[:plen] != parts[:plen]:         # Prefix doesn't match
                    continue
                elif len(args) <= len(parts):           # Command name
                    comp.append(parts[len(args) - 1])
                elif not cmd_only:                      # Arguments
                    if cmd[3] is None:
                        return []
                    return cmd[3](args[len(parts):]) or []
        return comp

    def execute_command(self, *args):
        """Execute a command given by a list of arguments."""
        args = list(args)
        for provider in self.providers:
            for cmd in provider.get_admin_commands() or []:
                parts = cmd[0].split()
                if args[:len(parts)] == parts:
                    f = cmd[4]
                    fargs = args[len(parts):]
                    try:
                        return f(*fargs)
                    except AdminCommandError as e:
                        e.cmd = ' '.join(parts)
                        raise
                    except TypeError:
                        tb = traceback.extract_tb(sys.exc_info()[2])
                        if len(tb) == 1:
                            raise AdminCommandError("Invalid arguments",
                                                    show_usage=True,
                                                    cmd=' '.join(parts))
                        raise
        raise AdminCommandError("Command not found", show_usage=True)
