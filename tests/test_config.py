# -*- coding: utf-8 -*-

import shutil
import os
import tempfile
import time

import pytest
from plumbum.config import (
    Configuration, ConfigurationError, Option, IntOption, BoolOption,
    FloatOption, ListOption, ChoiceOption, PathOption, ExtensionOption
)
from plumbum.core import Component, ComponentMeta, Interface, implements
from plumbum.util.file import wait_for_file_mtime_change
from plumbum.util.datefmt import time_now


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

    def test_read_and_getextensionoption(self):
        self._write(['[a]', 'option = ImplA', 'invalid = ImplB'])
        config = self._read()

        class IDummy(Interface):
            pass

        class ImplA(Component):
            implements(IDummy)

        class Foo(Component):
            default1 = (ExtensionOption)('a', 'default1', IDummy)
            default2 = (ExtensionOption)('a', 'default2', IDummy, 'ImplA')
            default3 = (ExtensionOption)('a', 'default3', IDummy, 'ImplB')
            option = (ExtensionOption)('a', 'option', IDummy)
            option2 = (ExtensionOption)('a', 'option', IDummy, 'ImplB')
            invalid = (ExtensionOption)('a', 'invalid', IDummy)

            def __init__(self):
                self.config = config

        self.env.enable_component(ImplA)
        self.env.enable_component(Foo)

        foo = Foo(self.env)
        self.assertRaises(ConfigurationError, getattr, foo, 'default1')
        self.assertIsInstance(foo.default2, ImplA)
        self.assertRaises(ConfigurationError, getattr, foo, 'default3')
        self.assertIsInstance(foo.option, ImplA)
        self.assertIsInstance(foo.option2, ImplA)
        self.assertRaises(ConfigurationError, getattr, foo, 'invalid')

    def test_read_and_getorderedextensionsoption(self):
        self._write(['[a]', 'option = ImplA, ImplB',
                     'invalid = ImplB, ImplD'])
        config = self._read()

        class IDummy(Interface):
            pass

        class ImplA(Component):
            implements(IDummy)

        class ImplB(Component):
            implements(IDummy)

        class ImplC(Component):
            implements(IDummy)

        class Foo(Component):
            # enclose in parentheses to avoid messages extraction
            default1 = (OrderedExtensionsOption)('a', 'default1', IDummy,
                                                 include_missing=False)
            default2 = (OrderedExtensionsOption)('a', 'default2', IDummy)
            default3 = (OrderedExtensionsOption)('a', 'default3', IDummy,
                                                 'ImplB, ImplC',
                                                 include_missing=False)
            option = (OrderedExtensionsOption)('a', 'option', IDummy,
                                               include_missing=False)
            invalid = (OrderedExtensionsOption)('a', 'invalid', IDummy)

            def __init__(self):
                self.config = config

        self.env.enable_component(ImplA)
        self.env.enable_component(ImplB)
        self.env.enable_component(ImplC)
        self.env.enable_component(Foo)

        foo = Foo(self.env)
        self.assertEqual([], foo.default1)
        self.assertEqual(3, len(foo.default2))
        self.assertIsInstance(foo.default2[0], ImplA)
        self.assertIsInstance(foo.default2[1], ImplB)
        self.assertIsInstance(foo.default2[2], ImplC)
        self.assertEqual(2, len(foo.default3))
        self.assertIsInstance(foo.default3[0], ImplB)
        self.assertIsInstance(foo.default3[1], ImplC)
        self.assertEqual(2, len(foo.option))
        self.assertIsInstance(foo.option[0], ImplA)
        self.assertIsInstance(foo.option[1], ImplB)
        self.assertRaises(ConfigurationError, getattr, foo, 'invalid')

    def test_getpath(self):
        base = os.path.dirname(self.filename)
        config = self._read()
        config.set('a', 'path_a', os.path.join(base, 'here', 'absolute.txt'))
        config.set('a', 'path_b', 'thisdir.txt')
        config.set('a', 'path_c', os.path.join(os.pardir, 'parentdir.txt'))
        self.assertEqual(os.path.join(base, 'here', 'absolute.txt'),
                         config.getpath('a', 'path_a'))
        self.assertEqual(os.path.join(base, 'thisdir.txt'),
                         config.getpath('a', 'path_b'))
        self.assertEqual(os.path.join(os.path.dirname(base), 'parentdir.txt'),
                         config.getpath('a', 'path_c'))

    def test_set_raises(self):
        class Foo(object):
            option = Option('a', 'option', 'value')

        f = Foo()
        self.assertRaises(AttributeError, setattr, f, 'option',
                          Option('a', 'option2', 'value2'))

    def test_set_and_save(self):
        config = self._read()
        config.set('b', u'öption0', 'y')
        config.set(u'aä', 'öption0', 'x')
        config.set('aä', 'option2', "Voilà l'été")  # UTF-8
        config.set(u'aä', 'option1', u"Voilà l'été") # unicode
        section = config['b']
        section.set('option1', None)
        section = config[u'aä']
        section.set('öption1', 'z')
        section.set('öption2', None)
        # Note: the following would depend on the locale.getpreferredencoding()
        # config.set('a', 'option3', "Voil\xe0 l'\xe9t\xe9") # latin-1
        self.assertEqual('x', config.get(u'aä', u'öption0'))
        self.assertEqual(u"Voilà l'été", config.get(u'aä', 'option1'))
        self.assertEqual(u"Voilà l'été", config.get(u'aä', 'option2'))
        self.assertEqual('', config.get('b', 'option1'))
        self.assertEqual('z', config.get(u'aä', 'öption1'))
        self.assertEqual('', config.get(u'aä', 'öption2'))
        config.save()

        self.assertEqual(['# -*- coding: utf-8 -*-\n',
                          '\n',
                          '[aä]\n',
                          "option1 = Voilà l'été\n",
                          "option2 = Voilà l'été\n",
                          'öption0 = x\n',
                          'öption1 = z\n',
                          'öption2 = \n',
                          # "option3 = VoilÃ  l'Ã©tÃ©\n",
                          '\n',
                          '[b]\n',
                          'option1 = \n',
                          'öption0 = y\n',
                          '\n'], readlines(self.filename))
        config2 = Configuration(self.filename)
        self.assertEqual('x', config2.get(u'aä', u'öption0'))
        self.assertEqual(u"Voilà l'été", config2.get(u'aä', 'option1'))
        self.assertEqual(u"Voilà l'été", config2.get(u'aä', 'option2'))
        # self.assertEqual(u"Voilà l'été", config2.get('a', 'option3'))

    def test_set_and_save_inherit(self):
        with self.inherited_file():
            self._write(['[a]', 'option = x'], site=True)
            config = self._read()
            config.set('a', 'option2', "Voilà l'été")  # UTF-8
            config.set('a', 'option1', u"Voilà l'été") # unicode
            self.assertEqual('x', config.get('a', 'option'))
            self.assertEqual(u"Voilà l'été", config.get('a', 'option1'))
            self.assertEqual(u"Voilà l'été", config.get('a', 'option2'))
            config.save()

            self.assertEqual(['# -*- coding: utf-8 -*-\n',
                              '\n',
                              '[a]\n',
                              "option1 = Voilà l'été\n",
                              "option2 = Voilà l'été\n",
                              '\n',
                              '[inherit]\n',
                              "file = trac-site.ini\n",
                              '\n'], readlines(self.filename))
            config2 = Configuration(self.filename)
            self.assertEqual('x', config2.get('a', 'option'))
            self.assertEqual(u"Voilà l'été", config2.get('a', 'option1'))
            self.assertEqual(u"Voilà l'été", config2.get('a', 'option2'))

    def test_set_and_save_inherit_remove_matching(self):
        """Options with values matching the inherited value are removed from
        the base configuration.
        """
        with self.inherited_file():
            self._write(['[a]', u'ôption = x'], site=True)
            config = self._read()
            self.assertEqual('x', config.get('a', u'ôption'))
            config.save()

            self.assertEqual(
                '# -*- coding: utf-8 -*-\n'
                '\n'
                '[inherit]\n'
                'file = trac-site.ini\n'
                '\n', read_file(self.filename))

            config.set('a', u'ôption', 'y')
            config.save()

            self.assertEqual(
                '# -*- coding: utf-8 -*-\n'
                '\n'
                '[a]\n'
                'ôption = y\n'
                '\n'
                '[inherit]\n'
                'file = trac-site.ini\n'
                '\n', read_file(self.filename))

            config.set('a', u'ôption', 'x')
            config.save()
            self.assertEqual(
                '# -*- coding: utf-8 -*-\n'
                '\n'
                '[inherit]\n'
                'file = trac-site.ini\n'
                '\n', read_file(self.filename))

    def test_simple_remove(self):
        self._write(['[a]', 'option = x'])
        config = self._read()
        config.get('a', 'option') # populates the cache
        config.set(u'aä', u'öption', u'öne')
        config.remove('a', 'option')
        self.assertEqual('', config.get('a', 'option'))
        config.remove(u'aä', u'öption')
        self.assertEqual('', config.get('aä', 'öption'))
        config.remove('a', 'option2') # shouldn't fail
        config.remove('b', 'option2') # shouldn't fail

    def test_sections(self):
        self._write(['[a]', 'option = x', '[b]', 'option = y'])
        config = self._read()
        self.assertEqual(['a', 'b'], config.sections())

        class Foo(object):
            # enclose in parentheses to avoid messages extraction
            section_c = (ConfigSection)('c', 'Doc for c')
            option_c = Option('c', 'option', 'value')

        self.assertEqual(['a', 'b', 'c'], config.sections())
        foo = Foo()
        foo.config = config
        self.assertTrue(foo.section_c is config['c'])
        self.assertEqual('value', foo.section_c.get('option'))

    def test_sections_unicode(self):
        self._write([u'[aä]', u'öption = x', '[b]', 'option = y'])
        config = self._read()
        self.assertEqual([u'aä', 'b'], config.sections())

        class Foo(object):
            option_c = Option(u'cä', 'option', 'value')

        self.assertEqual([u'aä', 'b', u'cä'], config.sections())

    def test_options(self):
        self._write(['[a]', 'option = x', '[b]', 'option = y'])
        config = self._read()
        self.assertEqual(('option', 'x'), iter(config.options('a')).next())
        self.assertEqual(('option', 'y'), iter(config.options('b')).next())
        self.assertRaises(StopIteration, iter(config.options('c')).next)
        self.assertEqual('option', iter(config['a']).next())
        self.assertEqual('option', iter(config['b']).next())
        self.assertRaises(StopIteration, iter(config['c']).next)

        class Foo(object):
            option_a = Option('a', 'b', 'c')

        self.assertEqual([('option', 'x'), ('b', 'c')],
                         list(config.options('a')))

    def test_options_unicode(self):
        self._write([u'[ä]', u'öption = x', '[b]', 'option = y'])
        config = self._read()
        self.assertEqual((u'öption', 'x'), iter(config.options(u'ä')).next())
        self.assertEqual(('option', 'y'), iter(config.options('b')).next())
        self.assertRaises(StopIteration, iter(config.options('c')).next)
        self.assertEqual(u'öption', iter(config['ä']).next())

        class Foo(object):
            option_a = Option(u'ä', u'öption2', 'c')

        self.assertEqual([(u'öption', 'x'), (u'öption2', 'c')],
                         list(config.options(u'ä')))

    def test_has_option(self):
        config = self._read()
        self.assertFalse(config.has_option('a', 'option'))
        self.assertFalse('option' in config['a'])
        self._write(['[a]', 'option = x'])
        config = self._read()
        self.assertTrue(config.has_option('a', 'option'))
        self.assertTrue('option' in config['a'])

        class Foo(object):
            option_a = Option('a', 'option2', 'x2')

        self.assertTrue(config.has_option('a', 'option2'))

    def test_has_option_unicode(self):
        config = self._read()
        self.assertFalse(config.has_option(u'ä', u'öption'))
        self.assertFalse(u'öption' in config[u'ä'])
        self._write([u'[ä]', u'öption = x'])
        config = self._read()
        self.assertTrue(config.has_option(u'ä', u'öption'))
        self.assertTrue(u'öption' in config[u'ä'])

        class Foo(object):
            option_a = Option(u'ä', u'öption2', 'x2')

        self.assertTrue(config.has_option(u'ä', u'öption2'))

    def test_reparse(self):
        self._write(['[a]', 'option = x'])
        config = self._read()
        self.assertEqual('x', config.get('a', 'option'))

        self._write(['[a]', 'option = y'])
        config.parse_if_needed()
        self.assertEqual('y', config.get('a', 'option'))

    def test_inherit_reparse(self):
        with self.inherited_file():
            self._write(['[a]', 'option = x'], site=True)
            config = self._read()
            self.assertEqual('x', config.get('a', 'option'))

            self._write(['[a]', 'option = y'], site=True)
            config.parse_if_needed()
            self.assertEqual('y', config.get('a', 'option'))

    def test_inherit_one_level(self):
        with self.inherited_file():
            self._write(['[a]', 'option = x'], site=True)
            config = self._read()
            self.assertEqual('x', config.get('a', 'option'))
            self.assertEqual(['a', 'inherit'], config.sections())
            config.remove('a', 'option') # Should *not* remove option in parent
            self.assertEqual('x', config.get('a', 'option'))
            self.assertEqual([('option', 'x')], list(config.options('a')))
            self.assertTrue('a' in config)

    def test_inherit_multiple(self):
        class Foo(object):
            option_b = Option('b', 'option2', 'default')
        base = os.path.dirname(self.filename)
        relsite1 = os.path.join('sub1', 'trac-site1.ini')
        site1 = os.path.join(base, relsite1)
        relsite2 = os.path.join('sub2', 'trac-site2.ini')
        site2 = os.path.join(base, relsite2)
        os.mkdir(os.path.dirname(site1))
        create_file(site1, '[a]\noption1 = x\n'
                           '[c]\noption = 1\npath1 = site1\n')
        try:
            os.mkdir(os.path.dirname(site2))
            create_file(site2, '[b]\noption2 = y\n'
                               '[c]\noption = 2\npath2 = site2\n')
            try:
                self._write(['[inherit]',
                             'file = %s, %s' % (relsite1, relsite2)])
                config = self._read()
                self.assertEqual('x', config.get('a', 'option1'))
                self.assertEqual('y', config.get('b', 'option2'))
                self.assertEqual('1', config.get('c', 'option'))
                self.assertEqual(os.path.join(base, 'site1'),
                                 config.getpath('c', 'path1'))
                self.assertEqual(os.path.join(base, 'site2'),
                                 config.getpath('c', 'path2'))
                self.assertEqual('',
                                 config.getpath('c', 'path3'))
                self.assertEqual(os.path.join(base, 'site4'),
                                 config.getpath('c', 'path4', 'site4'))
            finally:
                os.remove(site2)
                os.rmdir(os.path.dirname(site2))
        finally:
            os.remove(site1)
            os.rmdir(os.path.dirname(site1))

    def test_option_with_raw_default(self):
        class Foo(object):
            # enclose in parentheses to avoid messages extraction
            option_none = (Option)('a', 'none', None)
            option_blah = (Option)('a', 'blah', u'Blàh!')
            option_true = (BoolOption)('a', 'true', True)
            option_false = (BoolOption)('a', 'false', False)
            option_list = (ListOption)('a', 'list', ['#cc0', 4.2, 42, 0, None,
                                                     True, False, None],
                                       sep='|', keep_empty=True)
            option_list = (ListOption)('a', 'list-seps',
                                       ['#cc0', 4.2, 42, 0, None, True, False,
                                        None],
                                       sep=(',', '|'), keep_empty=True)
            option_choice = (ChoiceOption)('a', 'choice', [-42, 42])

        config = self._read()
        config.set_defaults()
        config.save()
        with open(self.filename, 'r') as f:
            assert f.next() == '# -*- coding: utf-8 -*-\n'
            assert f.next() == '\n'
            assert f.next() == '[a]\n'
            assert f.next() == 'blah = Blàh!\n'
            assert f.next() == 'choice = -42\n'
            assert f.next() == 'false = disabled\n'
            assert f.next() == 'list = #cc0|4.2|42|0||enabled|disabled|\n'
            assert f.next() == 'list-seps = #cc0,4.2,42,0,,enabled,disabled,\n'
            assert f.next() == 'none = \n'
            assert f.next() == 'true = enabled\n'
            assert f.next() == '\n'
            self.assertRaises(StopIteration, f.next)

    def test_unicode_option_with_raw_default(self):
        class Foo(object):
            # enclose in parentheses to avoid messages extraction
            option_none = (Option)(u'résumé', u'nöné', None)
            option_blah = (Option)(u'résumé', u'bláh', u'Blàh!')
            option_true = (BoolOption)(u'résumé', u'trüé', True)
            option_false = (BoolOption)(u'résumé', u'fálsé', False)
            option_list = (ListOption)(u'résumé', u'liśt',
                                       [u'#ccö', 4.2, 42, 0, None, True,
                                        False, None],
                                       sep='|', keep_empty=True)
            option_choice = (ChoiceOption)(u'résumé', u'chöicé', [-42, 42])

        config = self._read()
        config.set_defaults()
        config.save()
        with open(self.filename, 'r') as f:
            assert f.next() == '# -*- coding: utf-8 -*-\n'
            assert f.next() == '\n'
            assert f.next() == '[résumé]\n'
            assert f.next() == 'bláh = Blàh!\n'
            assert f.next() == 'chöicé = -42\n'
            assert f.next() == 'fálsé = disabled\n'
            assert f.next() == 'liśt = #ccö|4.2|42|0||enabled|disabled|\n'
            assert f.next() == 'nöné = \n'
            assert f.next() == 'trüé = enabled\n'
            assert f.next() == '\n'
            self.assertRaises(StopIteration, f.next)

    def test_option_with_non_normal_default(self):
        class Foo(object):
            # enclose in parentheses to avoid messages extraction
            option_int_0 = (IntOption)('a', 'int-0', 0)
            option_float_0 = (FloatOption)('a', 'float-0', 0)
            option_bool_1 = (BoolOption)('a', 'bool-1', '1')
            option_bool_0 = (BoolOption)('a', 'bool-0', '0')
            option_bool_yes = (BoolOption)('a', 'bool-yes', 'yes')
            option_bool_no = (BoolOption)('a', 'bool-no', 'no')

        expected = [
            '# -*- coding: utf-8 -*-\n',
            '\n',
            '[a]\n',
            'bool-0 = disabled\n',
            'bool-1 = enabled\n',
            'bool-no = disabled\n',
            'bool-yes = enabled\n',
            'float-0 = 0.0\n',
            'int-0 = 0\n',
            '\n',
        ]

        config = self._read()
        config.set_defaults()
        config.save()
        assert readlines(self.filename) == expected

        config.set('a', 'bool-1', 'True')
        config.save()
        assert readlines(self.filename) == expected

    def test_save_changes_mtime(self):
        """Test that each save operation changes the file modification time."""
        class Foo(object):
            IntOption('section', 'option', 1)
        sconfig = self._read()
        sconfig.set_defaults()
        sconfig.save()
        rconfig = self._read()
        assert rconfig.getint('section', 'option') == 1
        sconfig.set('section', 'option', 2)
        time.sleep(1.0 - time_now() % 1.0)
        sconfig.save()
        rconfig.parse_if_needed()
        assert rconfig.getint('section', 'option') == 2

    def test_touch_changes_mtime(self):
        """Test that each touch command changes the file modification time."""
        config = self._read()
        time.sleep(1.0 - time_now() % 1.0)
        config.touch()
        mtime = os.stat(self.filename).st_mtime
        config.touch()
        assert os.stat(self.filename).st_mtime != mtime


class ConfigurationSetDefaultsTestCase(BaseTest):
    """Tests for the `set_defaults` method of the `Configuration` class."""

    def setup_method(self, method):
        super(ConfigurationSetDefaultsTestCase, self).setup_method(method)

        class CompA(Component):
            opt1 = Option('compa', 'opt1', 1)
            opt2 = Option('compa', 'opt2', 'a')

        class CompB(Component):
            opt3 = Option('compb', 'opt3', 2)
            opt4 = Option('compb', 'opt4', 'b')

    def test_component_module_no_match(self):
        """No defaults written if component doesn't match."""
        config = self._read()
        config.set_defaults(component='trac.tests.conf')
        config.save()

        with open(self.filename, 'r') as f:
            assert f.next() == '# -*- coding: utf-8 -*-\n'
            assert f.next() == '\n'
            with pytest.raises(StopIteration):
                f.next()

    def test_component_class_no_match(self):
        """No defaults written if module doesn't match."""
        config = self._read()
        config.set_defaults(component='trac.tests.conf.CompC')
        config.save()

        with open(self.filename, 'r') as f:
            assert f.next() == '# -*- coding: utf-8 -*-\n'
            assert f.next() == '\n'
            with pytest.raises(StopIteration):
                f.next()

    def test_component_module_match(self):
        """Defaults of components in matching module are written."""
        config = self._read()
        config.set_defaults(component='trac.tests.config')
        config.save()

        with open(self.filename, 'r') as f:
            assert f.next() == '# -*- coding: utf-8 -*-\n'
            assert f.next() == '\n'
            assert f.next() == '[compa]\n'
            assert f.next() == 'opt1 = 1\n'
            assert f.next() == 'opt2 = a\n'
            assert f.next() == '\n'
            assert f.next() == '[compb]\n'
            assert f.next() == 'opt3 = 2\n'
            assert f.next() == 'opt4 = b\n'
            assert f.next() == '\n'
            with pytest.raises(StopIteration):
                f.next()

    def test_component_module_wildcard_match(self):
        """Defaults of components in matching module are written.
        Trailing dot-star are stripped in performing match.
        """
        config = self._read()
        config.set_defaults(component='trac.tests.config.*')
        config.save()

        with open(self.filename, 'r') as f:
            assert f.next() == '# -*- coding: utf-8 -*-\n'
            assert f.next() == '\n'
            assert f.next() == '[compa]\n'
            assert f.next() == 'opt1 = 1\n'
            assert f.next() == 'opt2 = a\n'
            assert f.next() == '\n'
            assert f.next() == '[compb]\n'
            assert f.next() == 'opt3 = 2\n'
            assert f.next() == 'opt4 = b\n'
            assert f.next() == '\n'
            with pytest.raises(StopIteration):
                f.next()

    def test_component_class_match(self):
        """Defaults of matching component are written."""
        config = self._read()
        config.set_defaults(component='trac.tests.config.CompA')
        config.save()

        with open(self.filename, 'r') as f:
            assert f.next() == '# -*- coding: utf-8 -*-\n'
            assert f.next() == '\n'
            assert f.next() == '[compa]\n'
            assert f.next() == 'opt1 = 1\n'
            assert f.next() == 'opt2 = a\n'
            assert f.next() == '\n'
            with pytest.raises(StopIteration):
                f.next()

    def test_component_no_overwrite(self):
        """Values in configuration are not overwritten."""
        config = self._read()
        config.set('compa', 'opt1', 3)
        config.save()
        config.set_defaults(component='trac.tests.config.CompA')
        config.save()

        with open(self.filename, 'r') as f:
            assert f.next() == '# -*- coding: utf-8 -*-\n'
            assert f.next() == '\n'
            assert f.next() == '[compa]\n'
            assert f.next() == 'opt1 = 3\n'
            assert f.next() == 'opt2 = a\n'
            assert f.next() == '\n'
            with pytest.raises(StopIteration):
                f.next()

    def test_component_no_overwrite_parent(self):
        """Values in parent configuration are not overwritten."""
        parent_config = Configuration(self.sitename)
        parent_config.set('compa', 'opt1', 3)
        parent_config.save()
        config = self._read()
        config.set('inherit', 'file', 'trac-site.ini')
        config.save()
        config.parse_if_needed(True)
        config.set_defaults(component='trac.tests.config.CompA')
        config.save()

        with open(self.sitename, 'r') as f:
            assert f.next() == '# -*- coding: utf-8 -*-\n'
            assert f.next() == '\n'
            assert f.next() == '[compa]\n'
            assert f.next() == 'opt1 = 3\n'
            assert f.next() == '\n'
            with pytest.raises(StopIteration):
                f.next()

        with open(self.filename, 'r') as f:
            assert f.next() == '# -*- coding: utf-8 -*-\n'
            assert f.next() == '\n'
            assert f.next() == '[compa]\n'
            assert f.next() == 'opt2 = a\n'
            assert f.next() == '\n'
            assert f.next() == '[inherit]\n'
            assert f.next() == 'file = trac-site.ini\n'
            assert f.next() == '\n'
            with pytest.raises(StopIteration):
                f.next()
