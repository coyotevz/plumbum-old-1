# -*- coding: utf-8 -*-

import sys
import os
import errno
import time
import random
import tempfile


can_rename_open_file = False
if os.name == 'nt':
    def _rename(src, dst):
        return False

    def _rename_atomic(src, dst):
        return False

    try:
        import ctypes
        MOVEFILE_REPLACE_EXISTING = 0x1
        MOVEFILE_WRITE_THROUGH = 0x8
        MoveFileEx = ctypes.windll.kernel32.MoveFileExW

        def _rename(src, dst):
            if _rename_atomic(src, dst):
                return True
            return MoveFileEx(src, dst, MOVEFILE_REPLACE_EXISTING |
                                        MOVEFILE_WRITE_THROUGH)

        CreateTransaction = ctypes.windll.ktmw32.CreateTransaction
        CommitTransaction = ctypes.windll.ktmw32.CommitTransaction
        MoveFileTransacted = ctypes.windll.kernel32.MoveFileTransactedW
        CloseHandle = ctypes.windll.kernel32.CloseHandle
        can_rename_open_file = True

        def _rename_atomic(src, dst):
            ta = CreateTransaction(None, 0, 0, 0, 0, 10000, 'Plumbum rename')
            if ta == -1:
                return False
            try:
                return (MoveFileTransacted(src, dst, None, None,
                                           MOVEFILE_REPLACE_EXISTING |
                                           MOVEFILE_WRITE_THROUGH, ta)
                        and CommitTransaction(ta))
            finally:
                CloseHandle(ta)
    except Exception:
        pass

    def rename(src, dst):
        # Try atomic or pseudo-atomic rename
        if _rename(src, dst):
            return
        # Fallback to "move away and replace"
        try:
            os.rename(src, dst)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
            old = "%s-%08x" % (dst, random.randint(0, sys.maxint))
            os.rename(dst, old)
            os.rename(src, dst)
            try:
                os.unlink(old)
            except Exception:
                pass
else:
    rename = os.rename
    can_rename_open_file = True


if os.name == 'nt':
    def touch_file(filename):
        """Upadte modified time of the given file. The file is created if
        missing.
        """
        # Use f.truncate() to avoid low resolution of GetSystemTime() on
        # Windows
        with open(filename, 'ab') as f:
            stat = os.fstat(f.fileno())
            f.truncate(stat.st_size)
else:
    def touch_file(filename):
        """Upadte modified time of the given file. The file is created if
        missing.
        """
        try:
            os.utime(filename, None)
        except OSError as e:
            if e.errno == errno.ENOENT:
                with open(filename, 'ab'):
                    pass


def wait_for_file_mtime_change(filename):
    """This function is typically called before a file save operation, waiting
    if necessary for the file modification time to change. The purpose it to
    avoid successive file updates going undetected by the caching mecanism that
    depends on a change in the file modification time to know when the file
    should be reparsed.
    """
    try:
        mtime = os.stat(filename).st_mtime
        touch_file(filename)
        while mtime == os.stat(filename).st_mtime:
            time.sleep(1e-3)
            touch_file(filename)
    except OSError:
        pass  # file doesn't exist yet


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
