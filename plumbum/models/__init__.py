# -*- coding: utf-8 -*-

from plumbum.lib.saw import SQLAlchemy


db = SQLAlchemy()
db.configure(uri='postgres://plumbum-app:plumbum-app@perseo/plumbum-ng')
