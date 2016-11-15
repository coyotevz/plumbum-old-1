# -*- coding: utf-8 -*-

from plumbum.commands import BaseCommand


class InitCommand(BaseCommand):

    def run_command(self, args):
        print("Running init command")
