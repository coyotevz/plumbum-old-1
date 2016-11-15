# -*- coding: utf-8 -*-

import sys
import os

from argparse import ArgumentParser
from pkg_resources import iter_entry_points

from plumbum import __version__ as VERSION


class BaseCommand(object):

    cmd_name = None
    short_help = ''

    def __init__(self, cmd_name):
        self.cmd_name = cmd_name
        self.parser = ArgumentParser()

        self.parser.add_argument('--inst-path', metavar='PATH',
                                 help='path of plumbum instance to operate on')
        print("{} created with parser: {}".format(self.__class__.__name__, id(self.parser)))

    def run_command(self, args):
        print("Runinng command")

def usage(subcommands):
    text = 'Plumbum ' + VERSION + '\n'
    for cmd in subcommands:
        text += ' %-12s %s\n' % (cmd.cmd_name, cmd.short_help)
    text += ('\n'
        'Most of these commands require an isntance directory to work on.\n'
        'This directory can be specified using either the first argument,\n'
        'the --inst-path option or using PLUMBUM_INSTANCE evironment variable')
    sys.stderr.write(text)


def run_command(args):
    commands = {}
    for entry in iter_entry_points('plumbum.commands'):
        commands[entry.name] = entry.load()(entry.name)

    has_env_info = "PLUMBUM_INSTANCE" in os.environ
    if (has_env_info and len(args) < 2) or \
       (not has_env_info and len(args) < 3):
           usage(commands.values())
           sys.exit(1)
    if args[1] in commands:
        cmd_name = args.pop(1)
    elif args[2] in commands:
        cmd_name = args.pop(2)
    else:
        usage(commands.values())
        sys.exit(1)
    cmd = commands[cmd_name]
    return cmd.run_command(args[1:])

def main():
    run_command(sys.argv)

if __name__ == "__main__":
    main()
