"""
This module houses context managers to assist in the managing of state during
kivy-ios builds.
"""
from logging import getLogger
from contextlib import contextmanager
from os import getcwd, chdir, environ
from os.path import expanduser


logger = getLogger(__name__)


@contextmanager
def cd(newdir):
    """
    Set the current working directory to `newdir` for the duration of the
    context.
    """
    prevdir = getcwd()
    logger.info("cd {}".format(newdir))
    chdir(expanduser(newdir))
    try:
        yield
    finally:
        logger.info("cd {}".format(prevdir))
        chdir(prevdir)


@contextmanager
def python_path(newdir):
    """
    Set the PYTHONPATH environmnet variable to `newdir` for the duraiton of the
    context.
    """
    prevdir = environ.get("PYTHONPATH")
    logger.debug("Setting PYTHONPATH to {}".format(newdir))
    environ["PYTHONPATH"] = newdir
    try:
        yield
    finally:
        logger.debug("Setting PYTHONPATH to {}".format(prevdir))
        if prevdir is None:
            environ.pop("PYTHONPATH")
        else:
            environ["PYTHONPATH"] = prevdir
