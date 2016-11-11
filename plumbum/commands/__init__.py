# -*- coding: utf-8 -*-

import sys
import os

def run_command(args):
    print("Running comands for plumbum software")
    return

    commands = {}
    for entry in iter_entry_points('plumbum.commands'):
        commands[entry.name] = entry.load()(entry_name)

    has_env_info = os.environ.has_key("PLUMBUM_INSTANCE")
    if (has_env_info and len(args) < 2) or \
       (not has_env_info and len(args) < 3):
           print("show usage")
           sys.exit(1)

def main():
    run_command(sys.argv)

if __name__ == "__main__":
    main()
