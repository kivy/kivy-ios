# -*- coding: utf-8 -*-

"""
binaryornot.check
-----------------

Main code for checking if a file is binary or text.
"""

from .helpers import get_starting_chunk, is_binary_string


def is_binary(filename):
    """
    :param filename: File to check.
    :returns: True if it's a binary file, otherwise False.
    """
    chunk = get_starting_chunk(filename)
    return is_binary_string(chunk)
