# -*- coding: utf-8 -*-

import sys
import cmd
import io
import pkg_resources

from plumbum import __version__ as VERSION
from plumbum.command.api import PlumbumCommandError, PlumbumCommandManager
from plumbum.config import Configuration
from plumbum.core import PlumbumError
from plumbum.instance import PlumbumInstance
from plumbum.util.text import printerr, printout


PB_VERSION = pkg_resources.get_distribution('Plumbum').version


class PlumbumCommand(cmd.Cmd):
    intro = ''
    doc_header = 'Plumbum Console %(version)s\n' \
                 'Available Commands:\n' \
                 % {'version': PB_VERSION}
    ruler = ''
    prompt = "Pb> "

    def __init__(self, instdir=None):
        cmd.Cmd.__init__(self)
        self.interactive = False


def _run(args):
    if args is None:
        args = sys.argv[1:]
    if sys.flags.optimize != 0:
        printerr("Python with optimizations is not supported.")
        return 2
    command = PlumbumCommand()
    return command.onecmd("help")


def run(args=None):
    """Main entry point."""
    return _run(args)


if __name__ == "__main__":
    pkg_resources.require('Plumbum==%s' % VERSION)
    sys.exit(run())
