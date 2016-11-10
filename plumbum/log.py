# -*- coding: utf-8 -*-

import logging
import logging.handlers
import sys


LOG_TYPES = ('none', 'stderr', 'file', 'syslog', 'eventlog')
LOG_TYPE_ALIASES = ('winlog', 'nteventlog', 'unix')
LOG_LEVELS = ('CRITICAL', 'ERROR', 'WARNINGS', 'INFO', 'DEBUG')
LOG_LEVEL_ALIASES = ('WARN', 'ALL')

LOG_LEVEL_MAP = {
    'DEBUG': logging.DEBUG, 'ALL': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING, 'WARN': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL,
}


def logger_handler_factory(logtype='syslog', logfile=None, level='WARNING',
                           logid='Plumbum', format=None):
    logger = logging.getLogger(logid)
    logtype = logtype.lower()
    if logtype == 'file':
        hdlr = logging.FileHandler(logfile)
    elif logtype in ('eventlog', 'winlog', 'nteventlog'):
        # Requires win32 extensions
        hdlr = logging.handlers.NTEventLogHandler(logid, logtype='Application')
    elif logtype in ('syslog', 'unix'):
        hdlr = logging.handlers.SysLogHandler('/dev/log')
    elif logtype == 'stderr':
        hdlr = logging.StreamHandler(sys.stderr)
    else:
        hdlr = logging.NullHandler()

    level = level.upper()
    level_as_int = LOG_LEVEL_MAP.get(level)
    if level_as_int is None:
        # Should never be reached because level is restricted through
        # ChoiceOption, therefore message is intentionaly left untranslated
        raise AssertionError("Unrecognized log level `{}`".format(level))
    logger.setLevel(level_as_int)

    if not format:
        format = 'Plumbum[%(module)s] %(levelname)s: %(message)s'
        if logtype in ('file', 'stderr'):
            format = '%(asctime)s ' + format
    datefmt = '%X' if logtype == 'stderr' else ''
    formatter = logging.Formatter(format, datefmt)
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)

    return logger


def shutdown(logger):
    for handler in logger.handlers[:]:
        handler.flush()
        handler.close()
        logger.removeHandler(handler)
