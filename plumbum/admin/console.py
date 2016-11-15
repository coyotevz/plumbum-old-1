# -*- coding: utf-8 -*-

import sys
import cmd

from plumbum import __version__ as VERSION


class PlumbumAdmin(cmd.Cmd):
    intro = ''
    doc_header = 'Plumbum Admin Console %(version)s\n' \
                 'Available Commands:\n'.format(version=VERSION)
    ruler = ''
    prompt = 'PB>'

    def __init__(self):
        cmd.Cmd.__init__(self)
        self.interactive = False

    def run(self):
        self.interactive = True
        self.cmdloop()

    ## Available Commands
    _help_help = [('help', '', 'Show documentation')]

    def do_help(self, line=None):
        print("plumbum-admin - The Plumbum Administration Console {version}"\
              .format(version=VERSION))
        if not self.interactive:
            print()
            print("Usage: plumbum-admin </path/to/instance> "
                    "[command [subcommand] [option ...]]\n")
            print("Invoking plumbum-admin without command starts "
                  "interative mode.")

    _help_quit = [('quit', '', 'Exit the program')]
    _help_exit = _help_quit
    _help_EOF = _help_quit

    def do_quit(self, line):
        print()
        sys.exit()

    do_exit = do_quit # Alias
    do_EOF = do_quit  # Alias


def run(args):
    if args is None:
        args = sys.argv[:1]

    admin = PlumbumAdmin()

    return admin.onecmd("help")


def main(args=None):
    return run(args)

if __name__ == "__main__":
    pkg_resources.require('Plumbum==%s' % VERSION)
    sys.exit(main())
