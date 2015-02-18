# -*- coding: utf-8 -*-

"""
binaryornot.helpers
-------------------

Helper utilities used by BinaryOrNot.
"""
def print_as_hex(s):
    """
    Print a string as hex bytes.
    """

    print(":".join("{0:x}".format(ord(c)) for c in s))


def get_starting_chunk(filename, length=1024):
    """
    :param filename: File to open and get the first little chunk of.
    :param length: Number of bytes to read, default 1024.
    :returns: Starting chunk of bytes.
    """
    # Ensure we open the file in binary mode
    with open(filename, 'rb') as f:
        chunk = f.read(length)
        return chunk


_printable_extended_ascii = b'\n\r\t\f\b'
if bytes is str:
    # Python 2 means we need to invoke chr() explicitly
    _printable_extended_ascii += b''.join(map(chr, range(32, 256)))
else:
    # Python 3 means bytes accepts integer input directly
    _printable_extended_ascii += bytes(range(32, 256))

def is_binary_string(bytes_to_check):
    """
    :param bytes: A chunk of bytes to check.
    :returns: True if appears to be a binary, otherwise False.
    """
    # Uses a simplified version of the Perl detection algorithm,
    # based roughly on Eli Bendersky's translation to Python:
    # http://eli.thegreenplace.net/2011/10/19/perls-guess-if-file-is-text-or-binary-implemented-in-python/

    # This is biased slightly more in favour of deeming files as text
    # files than the Perl algorithm, since all ASCII compatible character
    # sets are accepted as text, not just utf-8

    # Empty files are considered text files
    if not bytes_to_check:
        return False

    # Check for NUL bytes first
    if b'\x00' in bytes_to_check:
        return True

    # Now check for a high percentage of ASCII control characters
    # Binary if control chars are > 30% of the string
    control_chars = bytes_to_check.translate(None, _printable_extended_ascii)
    nontext_ratio = float(len(control_chars)) / float(len(bytes_to_check))
    return nontext_ratio > 0.3
