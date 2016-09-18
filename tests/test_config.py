# -*- coding: utf-8 -*-

import shutil
import os
import tempfile

import pytest
from plumbum.config import (
    Configuration, ConfigurationError, Option, IntOption, BoolOption,
    FloatOption, ListOption, ChoiceOption, PathOption
)
from plumbum.core import Component, ComponentMeta, Interface, implements
from plumbum.util.compat import wait_for_file_mtime_change


def create_file(path, data='', mode='w'):
    """Create a new file with the given data.

    :data: string or iterable of strings.
    """
    with open(path, mode) as f:
        if data:
            # TODO: Encode data to utf-8
            if isinstance(data, str):
                f.write(data)
            else: # Assume iterable
                f.writelines(data)


def _write(filename, lines):
    wait_for_file_mtime_change(filename)
    create_file(filename, '\n'.join(lines + ['']))#.encode('utf-8'))


def _read(filename):
    return read_file(filename).decode('utf-8')


def readlines(filename):
    with open(filename, 'r') as f:
        return f.readlines()


def mkdtemp():
    """Create a temp directory with prefix `pb-testdir-` and return the
    directory name.
    """
    return os.path.realpath(tempfile.mkdtemp(prefix='pb-testdir-'))


class TestConfiguration(object):

    def setup_method(self, method):
        self.config = Configuration(None)
        self.config.parser.add_section('séction1')
        self.config.parser.set('séction1', 'öption1', 'cönfig-valué')
        self.config.parser.set('séction1', 'öption4', 'cönfig-valué')
        parent_config = Configuration(None)
        parent_config.parser.add_section('séction1')
        parent_config.parser.add_section('séction2')
        parent_config.parser.set('séction1', 'öption1', 'cönfig-valué')
        parent_config.parser.set('séction1', 'öption2', 'înherited-valué')
        parent_config.parser.set('séction2', 'öption2', 'înherited-valué')
        self.config.parents = [parent_config]

        class OptionClass(object):
            Option('séction1', 'öption1', 'dēfault-valué')
            Option('séction1', 'öption2', 'dēfault-valué')
            Option('séction1', 'öption3', 'dēfault-valué')
            Option('séction3', 'öption1', 'dēfault-valué')

    def test_get_from_config(self):
        """Value is retrieved from the config."""
        assert self.config.get('séction1', 'öption1') == 'cönfig-valué'

    def test_get_from_inherited(self):
        """Value not specified in the config is retrieved from the inherited
        config.
        """
        assert self.config.get('séction1', 'öption2') == 'înherited-valué'

    def test_get_from_default(self):
        """Value not specified in the config or the inherited config is
        retrieved from the option default.
        """
        assert self.config.get('séction1', 'öption3') == 'dēfault-valué'

    def test_get_is_cached(self):
        """Value is cached on first retrieval from the parser."""
        option1 = self.config.get('séction1', 'öption1')
        self.config.parser.set('séction1', 'öption1', 'cönfig-valué2')
        assert self.config.get('séction1', 'öption1') is option1

    def test_contains_from_config(self):
        """Contains returns `True` for section defined in config."""
        assert 'séction1' in self.config

    def test_contains_from_inherited(self):
        """Contains returns `True` for section defined in inherited config."""
        assert 'séction2' in self.config

    def test_contains_from_default(self):
        """Contains returns `True` for section defined in an option."""
        assert 'séction3' in self.config

    def test_remove_from_config(self):
        """Value is removed from configuration."""
        self.config.remove('séction1', 'öption4')
        parser = self.config.parser
        assert parser.has_option('séction1', 'öption4') == False
        assert self.config.get('séction1', 'öption4') == ''

    def test_remove_leaves_inherited_unchanged(self):
        """Value is not removed from inherited configuration."""
        self.config.remove('séction1', 'öption2')
        parser = self.config.parents[0].parser
        assert parser.has_option('séction1', 'öption1')
        assert self.config.get('séction1', 'öption2') == 'înherited-valué'

class BaseTest(object):

    def setup_method(self, method):
        self.tmpdir = mkdtemp()
        self.filename = os.path.join(self.tmpdir, 'plumbum-test.ini')
        self.sitename = os.path.join(self.tmpdir, 'plumbum-site.ini')
        self._write([])
        self._orig = {
            'ComponentMeta._components': ComponentMeta._components,
            'ComponentMeta._registry': ComponentMeta._registry,
            #'ConfigSection.registry': ConfigSection.registry,
            'Option.registry': Option.registry,
        }
        ComponentMeta._components = list(ComponentMeta._components)
        ComponentMeta._registry = dict((interface, list(classes))
                                       for interface, classes
                                       in ComponentMeta._registry.items())
        #ConfigSection.registry = {}
        Option.registry = {}

    def tardown_method(self, method):
        ComponentMeta._components = self._orig['ComponentMeta._components']
        ComponentMeta._registry = self._orig['ComponentMeta._registry']
        #ConfigSection.registry = self._orig['ConfigSection.registry']
        Option.registry = self._orig['Option.registry']
        shutil.rmtree(self.tmpdir)

    def _read(self):
        return Configuration(self.filename)

    def _write(self, lines, site=False):
        filename = self.sitename if site else self.filename
        _write(filename, lines)


class TestIntegration(BaseTest):

    def test_repr(self):
        assert repr(Configuration(None)) == '<Configuration None>'
        config = self._read()
        assert repr(config) == '<Configuration {}>'.format(self.filename)

    def test_default(self):
        config = self._read()
        assert config.get('a', 'option') == ''
        assert config.get('a', 'option', 'value') == 'value'

        class Foo(object):
            str_option = Option('a', 'option', 'value')
            none_option = Option('b', 'option', None)
            int_option = IntOption('b', 'int_option', 0)
            bool_option = BoolOption('b', 'bool_option', False)
            float_option = FloatOption('b', 'float_option', 0.0)
            list_option = ListOption('b', 'list_option', [])

        assert config.get('a', 'option') == 'value'
        assert config.get('b', 'option') == ''
        assert config.get('b', 'int_option') == '0'
        assert config.get('b', 'bool_option') == 'disabled'
        assert config.get('b', 'float_option') == '0.0'
        assert config.get('b', 'list_option') == ''

    def test_default_bool(self):
        config = self._read()
        assert config.getbool('a', 'option') is False
        assert config.getbool('a', 'option', 'yes') is True
        assert config.getbool('a', 'option', 1) is True

        class Foo(object):
            option_a = Option('a', 'option', 'true')

        assert config.getbool('a', 'option') is True

    def test_default_int(self):
        config = self._read()
        with pytest.raises(ConfigurationError):
            config.getint('a', 'option', 'b')
        assert config.getint('a', 'option') == 0
        assert config.getint('a', 'option', '1') == 1
        assert config.getint('a', 'option', 1) == 1

        class Foo(object):
            option_a = Option('a', 'option', '2')

        assert config.getint('a', 'option') == 2

    def test_default_float(self):
        config = self._read()
        with pytest.raises(ConfigurationError):
            config.getfloat('a', 'option', 'b')
        assert config.getfloat('a', 'option') == 0.0
        assert config.getfloat('a', 'option', '1.2') == 1.2
        assert config.getfloat('a', 'option', 1.2) == 1.2
        assert config.getfloat('a', 'option', 1) == 1.0

        class Foo(object):
            option_a = Option('a', 'option', '2.5')

        assert config.getfloat('a', 'option') == 2.5

    def test_default_path(self):
        config = self._read()
        class Foo(object):
            option_a = PathOption('a', 'opt1', 'file.ini')
            option_b = PathOption('a', 'opt2', '/somewhere/file.ini')
        assert config.get('a', 'opt1') == 'file.ini'
        assert config.getpath('a', 'opt1') != 'file.ini'
        assert os.path.isabs(config.getpath('a', 'opt1')) is True
        assert os.path.splitdrive(config.getpath('a', 'opt2'))[1]\
                .replace('\\', '/') == '/somewhere/file.ini'
        assert os.path.splitdrive(config.getpath('a', 'opt3', '/none.ini'))[1]\
                .replace('\\', '/') == '/none.ini'
        assert config.getpath('a', 'opt3', 'none.ini') != 'none.ini'

    def test_read_and_get(self):
        self._write(['[a]', 'option = x'])
        config = self._read()
        assert config.get('a', 'option') == 'x'
        assert config.get('a', 'option', 'y') == 'x'
        assert config.get('b', 'option2', 'y') == 'y'

    def test_read_and_get_unicode(self):
        self._write(['[ä]', 'öption = x'])
        config = self._read()
        assert config.get('ä', 'öption') == 'x'
        assert config.get('ä', 'öption', 'y') == 'x'
        assert config.get('b', 'öption2', 'y') == 'y'

    def test_read_and_getbool(self):
        self._write(['[a]', 'option = yes', 'option2 = true',
                     'option3 = eNaBlEd', 'option4 = on',
                     'option5 = 1', 'option6 = 123', 'option7 = 123.456',
                     'option8 = disabled', 'option9 = 0', 'option10 = 0.0'])
        config = self._read()
        assert config.getbool('a', 'option') == True
        assert config.getbool('a', 'option', False) == True
        assert config.getbool('a', 'option2') == True
        assert config.getbool('a', 'option3') == True
        assert config.getbool('a', 'option4') == True
        assert config.getbool('a', 'option5') == True
        assert config.getbool('a', 'option6') == True
        assert config.getbool('a', 'option7') == True
        assert config.getbool('a', 'option8') == False
        assert config.getbool('a', 'option9') == False
        assert config.getbool('a', 'option10') == False
        assert config.getbool('b', 'option_b') == False
        assert config.getbool('b', 'option_b', False) == False
        assert config.getbool('b', 'option_b', 'disabled') == False

    def test_read_and_getint(self):
        self._write(['[a]', 'option = 42'])
        config = self._read()
        assert config.getint('a', 'option') == 42
        assert config.getint('a', 'option', 25) == 42
        assert config.getint('b', 'option2') == 0
        assert config.getint('b', 'option2', 25) == 25
        assert config.getint('b', 'option2', '25') == 25

    def test_read_and_getfloat(self):
        self._write(['[a]', 'option = 42.5'])
        config = self._read()
        assert config.getfloat('a', 'option') == 42.5
        assert config.getfloat('a', 'option', 25.3) == 42.5
        assert config.getfloat('b', 'option2') == 0
        assert config.getfloat('b', 'option2', 25.3) == 25.3
        assert config.getfloat('b', 'option2', 25) == 25.0
        assert config.getfloat('b', 'option2', '25.3') == 25.3

    def test_read_and_getlist(self):
        self._write(['[a]', 'option = foo, bar, baz'])
        config = self._read()
        assert config.getlist('a', 'option') == ['foo', 'bar', 'baz']
        assert config.getlist('b', 'option2') == []
        assert config.getlist('b', 'option2', ['foo', 'bar', 'baz'])\
                == ['foo', 'bar', 'baz']
        assert config.getlist('b', 'option2', 'foo, bar, baz')\
                == ['foo', 'bar', 'baz']

    def test_read_and_getlist_sep(self):
        self._write(['[a]', 'option = foo | bar | baz'])
        config = self._read()
        assert config.getlist('a', 'option', sep='|') == ['foo', 'bar', 'baz']

    def test_read_and_getlist_keep_empty(self):
        self._write(['[a]', 'option = ,bar,baz'])
        config = self._read()
        assert config.getlist('a', 'option') == ['bar', 'baz']
        assert config.getlist('a', 'option', keep_empty=True)\
                == ['', 'bar', 'baz']

    def test_read_and_getlist_false_values(self):
        config = self._read()
        values = [None, False, '', 'foo', u'', u'bar',
                  0, 0, 0.0, 0j, 42, 43.0]
        assert config.getlist('a', 'false', values)\
                == [False, 'foo', u'bar', 0, 0, 0.0, 0j, 42, 43.0]
        assert config.getlist('a', 'false', values, keep_empty=True) == values

    def test_read_and_getlist_multi_seps(self):
        self._write(['[a]', 'option = 42 foo,bar||baz,||blah'])
        config = self._read()

        expected = ['42', 'foo', 'bar', 'baz', 'blah']
        assert config.getlist('a', 'option', '', sep=(' ', ',', '||'))\
                == expected
        assert config.getlist('a', 'option', '', sep=[' ', ',', '||'])\
                == expected

        assert config.getlist('a', 'option', '', sep=(' ', ',', '||'),
                keep_empty=True) == ['42', 'foo', 'bar', 'baz', '', 'blah']

        expected = ['42 foo,bar', 'baz,', 'blah']
        assert config.getlist('a', 'option', '', sep=['||']) == expected
        assert config.getlist('a', 'option', '', sep='||') == expected

    def test_read_and_choice(self):
        self._write(['[a]', 'option = 2', 'invalid = d',
                     '[û]', 'èncoded = à'])
        config = self._read()

        class Foo(object):
            # enclose in parentheses to avoid messages extraction
            option = (ChoiceOption)('a', 'option', ['Item1', 2, '3'])
            other = (ChoiceOption)('a', 'other', [1, 2, 3])
            invalid = (ChoiceOption)('a', 'invalid', ['a', 'b', 'c'])
            encoded = (ChoiceOption)('a', 'èncoded', ['à', 'ć', 'ē'])

            def __init__(self):
                self.config = config

        foo = Foo()
        assert foo.option == '2'
        assert foo.other == '1'
        assert foo.encoded == 'à'
        config.set('a', 'èncoded', 'ć')
        assert foo.encoded == 'ć'
        with pytest.raises(ConfigurationError):
            getattr(foo, 'invalid')
