# -*- coding: utf-8 -*-

import pytest
from plumbum.core import PlumbumError, Component, ComponentManager, ComponentMeta
from plumbum.core import implements, Interface, ExtensionPoint


def test_init_plumbum_error():
    e = PlumbumError("the message", "the title", True)
    assert e.message == "the message"
    assert e.title == "the title"
    assert e.show_traceback == True


class ITest(Interface):
    def test():
        """Dummy function."""


class IOtherTest(Interface):
    def other_test():
        """Other dummy function."""


class TestComponent(object):

    def setup_method(self, method):
        self.compmgr = ComponentManager()

        # Make sure we have not external components hanging around in the
        # component registry
        self.old_registry = ComponentMeta._registry
        ComponentMeta._registry = {}

    def teardown_method(self, method):
        ComponentMeta._registry = self.old_registry

    def test_base_class_not_registered(self):
        """Make sure that the Component base class does not appear in the
        component registry.
        """
        assert Component not in ComponentMeta._components
        with pytest.raises(PlumbumError):
            self.compmgr[Component]

    def test_abstract_component_not_registered(self):
        """Make sure that a Component class marked as abstract does not appear
        in the component registry.
        """
        class AbstractComponent(Component):
            abstract = True
        assert AbstractComponent not in ComponentMeta._components
        with pytest.raises(PlumbumError):
            self.compmgr[AbstractComponent]

    def test_unregistered_component(self):
        """Make sure the component manager refuses to manage classes not
        derived from `Component`.
        """
        class NoComponent(object):
            pass
        with pytest.raises(PlumbumError):
            self.compmgr[NoComponent]

    def test_component_registration(self):
        """Verify that classes derived from `Component` are managed by the
        component manager.
        """
        class ComponentA(Component):
            pass
        assert self.compmgr[ComponentA]
        assert ComponentA(self.compmgr)

    def test_component_identity(self):
        """Make sure instantiating a component multiple times just return the
        same instance again.
        """
        class ComponentA(Component):
            pass
        c1 = ComponentA(self.compmgr)
        c2 = ComponentA(self.compmgr)
        assert c1 is c2, "Expected same component instance"
        c2 = self.compmgr[ComponentA]
        assert c1 is c2, "Expected same component instance"

    def test_component_initializer(self):
        """Make sure that a component's `__init__` method gets called."""
        class ComponentA(Component):
            def __init__(self):
                self.data = 'test'
        assert ComponentA(self.compmgr).data == 'test'
        ComponentA(self.compmgr).data = 'newtest'
        assert ComponentA(self.compmgr).data == 'newtest'

    def test_inherited_component_initializer(self):
        """Makes sure that the `__init__` method of a component's super-class
        gets called if the component doesn't override it.
        """
        class ComponentA(Component):
            def __init__(self):
                self.data = 'foo'
        class ComponentB(ComponentA):
            def __init__(self):
                self.data = 'bar'
        class ComponentC(ComponentB):
            pass
        assert ComponentC(self.compmgr).data == 'bar'
        ComponentC(self.compmgr).data = 'baz'
        assert ComponentC(self.compmgr).data == 'baz'

    def test_implements_called_outside_classdef(self):
        """Verify that calling implements() outside a class definition raises
        an `AssertionError`.
        """
        with pytest.raises(AssertionError):
            implements()

    def test_implements_multiple(self):
        """Verify that a component 'implementing' an interface more than once
        (e.g. through inheritance) is not called more than on ce from an
        extension point.
        """
        log = []
        class Parent(Component):
            abstract = True
            implements(ITest)
        class Child(Parent):
            implements(ITest)
            def test(self):
                log.append("call")
        class Other(Component):
            tests = ExtensionPoint(ITest)
        for test in Other(self.compmgr).tests:
            test.test()
        assert log == ["call"]

    def test_attribute_access(self):
        """Verify that accessing undefined attributes on component raises an
        `AttributeError`.
        """
        class ComponentA(Component):
            pass
        comp = ComponentA(self.compmgr)
        with pytest.raises(AttributeError):
            comp.foo

    def test_nonconforming_extender(self):
        """Verify that accessing a method of declared extension point interface
        raises a normal `AttributeError` if the component does not implement
        the method.
        """
        class ComponentA(Component):
            tests = ExtensionPoint(ITest)
        class ComponentB(Component):
            implements(ITest)
        tests = iter(ComponentA(self.compmgr).tests)
        with pytest.raises(AttributeError):
            tests.next().test()

    def test_extension_point_with_no_extension(self):
        """Verify that accessing an extension point with no extenders returns
        an empty list.
        """
        class ComponentA(Component):
            test = ExtensionPoint(ITest)
        tests = iter(ComponentA(self.compmgr).test)
        with pytest.raises(StopIteration):
            next(tests)

    def test_extension_point_with_one_extension(self):
        """Verify that a single component extending an extension point can be
        accessed through the extension pint attribute of the declaring
        component.
        """
        class ComponentA(Component):
            tests = ExtensionPoint(ITest)
        class ComponentB(Component):
            implements(ITest)
            def test(self):
                return 'x'
        tests = iter(ComponentA(self.compmgr).tests)
        assert next(tests).test() == 'x'
        with pytest.raises(StopIteration):
            next(tests)

    def test_extension_point_with_two_extensions(self):
        """Verify that two components extending an extension point can be
        accessed through the extension point attribute of the declaring
        component.
        """
        class ComponentA(Component):
            tests = ExtensionPoint(ITest)
        class ComponentB(Component):
            implements(ITest)
            def test(self):
                return 'x'
        class ComponentC(Component):
            implements(ITest)
            def test(self):
                return 'y'
        results = [test.test() for test in ComponentA(self.compmgr).tests]
        assert sorted(results) == ['x', 'y']

    def test_inherited_extension_point(self):
        """Verify that extension pints are inherited to sub-classes."""
        class BaseComponent(Component):
            tests = ExtensionPoint(ITest)
        class ConcreteComponent(BaseComponent):
            pass
        class ExtendingComponent(Component):
            implements(ITest)
            def test(self):
                return 'x'
        tests = iter(ConcreteComponent(self.compmgr).tests)
        assert next(tests).test() == 'x'
        with pytest.raises(StopIteration):
            next(tests)

    def test_inherited_implements(self):
        """Verify that component with a super-class implementing an extension
        piont interface is also registeed as implementing that interface.
        """
        class BaseComponent(Component):
            implements(ITest)
            abstract = True
        class ConcreteComponent(BaseComponent):
            pass
        assert ConcreteComponent in ComponentMeta._registry.get(ITest, [])

    def test_inherited_implements_multilevel(self):
        """Verify that extension point interfaces are inherited for more than
        one level of inheritance.
        """
        class BaseComponent(Component):
            implements(ITest)
            abstract = True
        class ChildComponent(BaseComponent):
            implements(IOtherTest)
            abstract = True
        class ConcreteComponent(ChildComponent):
            pass
        assert ConcreteComponent in ComponentMeta._registry.get(ITest, [])
        assert ConcreteComponent in ComponentMeta._registry.get(IOtherTest, [])

    def test_component_manager_component(self):
        """Verify that a component manager can itself be a component with its
        own extension points.
        """
        class ManagerComponent(ComponentManager, Component):
            tests = ExtensionPoint(ITest)
            def __init__(self, foo, bar):
                ComponentManager.__init__(self)
                self.foo, self.bar = foo, bar
        class Extender(Component):
            implements(ITest)
            def test(self):
                return 'x'
        mgr = ManagerComponent('Test', 42)
        assert id(mgr) == id(mgr[ManagerComponent])
        tests = iter(mgr.tests)
        assert next(tests).test() == 'x'
        with pytest.raises(StopIteration):
            next(tests)

    def test_component_manager_component_isolation(self):
        """Verify that a component manager that is also a component will only
        be listed in extension points for components instantiated in its scope.
        """
        class ManagerComponentA(ComponentManager, Component):
            implements(ITest)
            def test(self):
                pass

        class ManagerComponentB(ManagerComponentA):
            pass

        class Tester(Component):
            tests = ExtensionPoint(ITest)

        mgrA = ManagerComponentA()
        mgrB = ManagerComponentB()

        assert Tester(mgrA).tests == [mgrA]
        assert Tester(mgrB).tests == [mgrB]

    def test_instantiation_doesnt_enabled(self):
        """Make sure that a component disable dby the ComponentManager is not
        implicitly enabled by instantiating it directly.
        """
        class DisablingComponentManager(ComponentManager):
            def is_component_enabled(self, cls):
                return False
        class ComponentA(Component):
            pass
        mgr = DisablingComponentManager()
        instance = ComponentA(mgr)
        assert mgr[ComponentA] is None

    def test_invalid_argument_raises(self):
        """Assertion Error is raised when  first argument to initializer is not
        a ComponentManager instance.
        """
        class ComponentA(Component):
            pass
        with pytest.raises(AssertionError):
            ComponentA()
