# -*- coding: utf-8 -*-

from plumbum.commands import BaseCommand

class CreateUserCommand(BaseCommand):

    cmd_name = 'createuser'
    short_help = 'create a system user'
    usage = 'createuser [options]'


class ListUsersCommand(BaseCommand):

    cmd_name = 'listusers'
    short_help = 'list existing users'
    usage = 'listusers [options]'
