# -*- coding: utf-8 -*-

import os
import tempfile

from plumbum.util.compat import rename


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


class AtomicFile(object):
    """A file that appears atomically with its full content.

    This file-like object writes to a temporary file in the same directory as
    the final file. If the file is commited, the temporary file is renamed
    atomically (on Unix, at least) to its final name. If it is rolled back, the
    temporary file is removed.
    """
    def __init__(self, path, mode='w', bufsize=-1):
        self._file = None
        self._path = os.path.realpath(path)
        dir, name = os.path.split(self._path)
        fd, self._temp = tempfile.mkstemp(prefix=name + '-', dir=dir)
        self._file = os.fdopen(fd, mode, bufsize)

        # Try to preserve permissions and group ownership, but failure should
        # not be fatal
        try:
            st = os.stat(self._path)
            if hasattr(os, 'chmod'):
                os.chmod(self._temp, st.st_mode)
            if hasattr(os, 'chflags') and hasattr(st, 'st_flags'):
                os.chflags(self._temp, st.st_flags)
            if hasattr(os, 'chown'):
                os.chown(self._temp, -1, st.st_gid)
        except OSError:
            pass

    def __getattr__(self, name):
        return getattr(self._file, name)

    def commit(self):
        if self._file is None:
            return
        try:
            f, self._file = self._file, None
            f.close()
            rename(self._temp, self._path)
        except Exception:
            os.unlink(self._temp)
            raise

    def rollback(self):
        if self._file is None:
            return
        try:
            f, self._file = self._file, None
            f.close()
        finally:
            try:
                os.unlink(self._temp)
            except Exception:
                pass

    close = commit
    __del__ = rollback

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    @property
    def closed(self):
        return self._file is None or self._file.closed
