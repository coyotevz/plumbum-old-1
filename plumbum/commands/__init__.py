# -*- coding: utf-8 -*-

import sys
import os

from pkg_resources import iter_entry_points

def run_command(args):
    print("Running tests commands for plumbum software")
    commands = {}
    for entry in iter_entry_points('plumbum.commands'):
        #commands[entry.name] = entry.load()(entry_name)
        print("Found entry: %s" % entry.name)

    has_env_info = "PLUMBUM_INSTANCE" in os.environ
    if (has_env_info and len(args) < 2) or \
       (not has_env_info and len(args) < 3):
           print("show usage")
           sys.exit(1)

def main():
    run_command(sys.argv)

if __name__ == "__main__":
    main()
