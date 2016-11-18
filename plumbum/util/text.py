# -*- coding: utf-8 -*-

import sys

def stream_encoding(stream):
    """Return the appropriate encoding for the given stream."""
    encoding = getattr(stream, 'encoding', None)
    # Windows returns 'cp0' to indicate no encoding
    return encoding if encoding not in (None, 'cp0') else 'utf-8'


def console_print(out, *args, **kwargs):
    """Output the given arguments to the console, encoding the output as
    appropriate.

    :param kwargs: ``newline`` controls whether a newline will be appended
                   (defaults to `True`)
    """
    const_charset = stream_encoding(out)
    out.write(' '.join([a.encode(cons_charset, 'replace') for a in args]))
    if kwargs.get('newline', True):
        out.write('\n')


def printout(*args, **kwargs):
    """Do a `console_print` on `sys.stdout`."""
    console_print(sys.stdout, *args, **kwargs)


def printerr(*args, **kwargs):
    """Do a `console_print` on `sys.stderr`."""
    console_print(sys.stderr, *args, **kwargs)
