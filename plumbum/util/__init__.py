# -*- coding: utf-8 -*-

import os
import functools

from plumbum.util.file import rename


def as_bool(value, default=False):
    """Convert the given value to a `bool`.

    If `value` is a string, return `True` for any of "yes", "true", "enabled",
    "on" or non-zero numbers, ignoring case. For non-string arguments, return
    the argument converted to a `bool`, or `default` if the conversion fails.
    """
    if isinstance(value, str):
        try:
            return bool(float(value))
        except ValueError:
            value = value.strip().lower()
            if value in ('yes', 'true', 'enabled', 'on'):
                return True
            elif value in ('no', 'false', 'disabled', 'off'):
                return False
            else:
                return default
    try:
        return bool(value)
    except (TypeError, ValueError):
        return default


def pathjoin(*args):
    """Strip `/` from the arguments and join them with a single `/`."""
    return '/'.join(filter(None, (each.strip('/') for each in args if each)))


def to_list(splittable, sep=','):
    """Split a string at `sep` and return a list without any empty items.
    """
    split = [x.strip() for x in splittable.split(sep)]
    return [item for item in split if item]


class lazy(object):
    """A lazily-evaluated attribute."""

    def __init__(self, fn):
        self.fn = fn
        functools.update_wrapper(self, fn)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        if self.fn.__name__ in instance.__dict__:
            return instance.__dict__[self.fn.__name__]
        result = self.fn(instance)
        instance.__dict__[self.fn.__name__] = result
        return result

    def __set__(self, instance, value):
        instance.__dict__[self.fn.__name__] = value

    def __delete__(self, instance):
        if self.fn.__name__ in instance.__dict__:
            del instance.__dict__[self.fn.__name__]
