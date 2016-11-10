# -*- coding: utf-8 -*-

import os
import shutil
import pytest
from configparser import ConfigParser

from plumbum.core import PlumbumError, ComponentManager, Component, implements
from plumbum.instance import PlumbumInstance
from plumbum.config import ConfigurationError
from plumbum.api import IInstanceSetupParticipant

from tests.utils import mkdtemp


class InstanceCreatedWithoutData(PlumbumInstance):

    def __init__(self, path, create=False, options=[]):
        ComponentManager.__init__(self)

        self.path = path
        self.href = self.abs_href = None

        if create:
            self.create(options)
        else:
            self.verify()
            self.setup_config()


def test_empty_instance():
    path = mkdtemp()
    instance = InstanceCreatedWithoutData(path, create=True)
    assert instance.database_version is False
    instance.shutdown()
    #shutil.rmtree(instance.path)


class TestPlumbumInstance(object):

    def setup_method(self):
        instance_path = mkdtemp()
        self.instance = PlumbumInstance(instance_path, create=True)
        self.instance.config.save()

    def teardown_method(self):
        self.instance.shutdown()
        #shutil.rmtree(self.instance.path)

    def test_missing_configfile_raises_plumbum_error(self):
        """PlumbumError is raised when config file is missing."""
        os.remove(self.instance.config_file_path)
        with pytest.raises(PlumbumError):
            PlumbumInstance(self.instance.path)

    # Some test with database versions

    def test_is_component_enabled(self):
        assert PlumbumInstance.required is True
        assert self.instance.is_component_enabled(PlumbumInstance)

    def test_dumped_values_in_plumbumini(self):
        parser = ConfigParser()
        filename = self.instance.config.filename
        assert parser.read(filename) == [filename]
        #assert parser.get('revisionlog', 'graph_colors') == \
        #        "#cc0,#0c0,#0cc,#00c,#c0c,#c00"
        #assert parser.get('plumbum', 'secure_cookies') == 'disabled'

    def test_dumped_values_in_plumbumini_sample(self):
        parser = ConfigParser()
        filename = self.instance.config.filename + '.sample'
        assert parser.read(filename) == [filename]
        #assert parser.get('revisionlog', 'graph_colors') == \
        #        "#cc0,#0c0,#0cc,#00c,#c0c,#c00"
        #assert parser.get('plumbum', 'secure_cookies') == 'disabled'
        assert parser.has_option('logging', 'log_format')
        assert parser.get('logging', 'log_format') == ''

    def test_invalid_log_level_raises_exception(self):
        self.instance.config.set('logging', 'log_level', 'invalid')
        self.instance.config.save()

        assert self.instance.config.get('logging', 'log_level') == 'invalid'
        #with pytest.raises(ConfigurationError):
        #    open_instance(self.instance.path, True)

    def test_ivalid_log_type_raises_exception(self):
        self.instance.config.set('logging', 'log_type', 'invalid')
        self.instance.config.save()

        assert self.instance.config.get('logging', 'log_type') == 'invalid'
        #with pytest.raises(ConfigurationError):
        #    open_instance(self.instance.path, True)

    def test_upgrade_instance(self):
        """InstanceSetupParticipants are called only if instance_needs_upgrade
        returns True for the participant."""

        class SetupParticipantA(Component):
            implements(IInstanceSetupParticipant)

            called = False

            def instance_created(self):
                pass

            def instance_needs_upgrade(self):
                return True

            def upgrade_instance(self):
                self.called = True

        class SetupParticipantB(Component):
            implements(IInstanceSetupParticipant)

            called = False

            def instance_created(self):
                pass

            def instance_needs_upgrade(self):
                return False

            def upgrade_instance(self):
                self.called = True

        self.instance.enable_component(SetupParticipantA)
        self.instance.enable_component(SetupParticipantB)
        participant_a = SetupParticipantA(self.instance)
        participant_b = SetupParticipantB(self.instance)

        assert self.instance.needs_upgrade()
        self.instance.upgrade()
        assert participant_a.called is True
        assert participant_b.called is False
