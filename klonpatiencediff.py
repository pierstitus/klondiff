#!/usr/bin/env python3
# Copyright (C) 2005, 2006, 2007 Canonical Ltd
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

import sys
PY3 = sys.version_info[0] == 3

import os
import sys
import time
import difflib
import re

__all__ = ['PatienceSequenceMatcher', 'unified_diff', 'unified_diff_files']


########################################################################
###  Binary file test
########################################################################

# A function that takes an integer in the 8-bit range and returns
# a single-character byte object in py3 / a single-character string
# in py2.
#
int2byte = (lambda x: bytes((x,))) if PY3 else chr

_text_characters = (
        b''.join(int2byte(i) for i in range(32, 127)) +
        b'\n\r\t\f\b')

def istext(block):
    """ Uses heuristics to guess whether the given file is text or binary,
        by reading a single block of bytes from the file.
        If more than 30% of the chars in the block are non-text, or there
        are NUL ('\x00') bytes in the block, assume this is a binary file.
    """
    if b'\x00' in block:
        # Files with null bytes are binary
        return False
    elif not block:
        # An empty file is considered a valid text file
        return True

    # Use translate's 'deletechars' argument to efficiently remove all
    # occurrences of _text_characters from the block
    nontext = block.translate(None, _text_characters)
    return float(len(nontext)) / len(block) <= 0.30

def binary_test(file1, file2, blocksize=512):
    with open(file1, 'rb') as f1:
        with open(file2, 'rb') as f2:
            block1 = f1.read(blocksize)
            block2 = f2.read(blocksize)

            if istext(block1) and istext(block2):
                return 'text'

            while block1 and block2 and block1 == block2:
                block1 = f1.read(blocksize)
                block2 = f2.read(blocksize)

            if block1 or block2:
                return 'binary_different'
            else:
                return 'binary_same'


########################################################################
###  Unified Diff
########################################################################

def _format_range_unified(start, stop):
    'Convert range to the "ed" format'
    # Per the diff spec at http://www.unix.org/single_unix_specification/
    beginning = start + 1     # lines start numbering with one
    length = stop - start
    if length == 1:
        return '{}'.format(beginning)
    if not length:
        beginning -= 1        # empty ranges begin at line just before the range
    return '{},{}'.format(beginning, length)

# This is a version of unified_diff which only adds a factory parameter
# so that you can override the default SequenceMatcher
# this has been submitted as a patch to python
def unified_diff(a, b, fromfile='', tofile='', fromfiledate='',
                 tofiledate='', n=3, lineterm='\n',
                 sequencematcher=None, function_regexp=r'^\w'):
    r"""
    Compare two sequences of lines; generate the delta as a unified diff.

    Unified diffs are a compact way of showing line changes and a few
    lines of context.  The number of context lines is set by 'n' which
    defaults to three.

    By default, the diff control lines (those with ---, +++, or @@) are
    created with a trailing newline.  This is helpful so that inputs
    created from file.readlines() result in diffs that are suitable for
    file.writelines() since both the inputs and outputs have trailing
    newlines.

    For inputs that do not have trailing newlines, set the lineterm
    argument to "" so that the output will be uniformly newline free.

    The unidiff format normally has a header for filenames and modification
    times.  Any or all of these may be specified using strings for
    'fromfile', 'tofile', 'fromfiledate', and 'tofiledate'.
    The modification times are normally expressed in the ISO 8601 format.

    Example:

    >>> for line in unified_diff('one two three four'.split(),
    ...             'zero one tree four'.split(), 'Original', 'Current',
    ...             '2005-01-26 23:30:50', '2010-04-02 10:20:52',
    ...             lineterm=''):
    ...     print line                  # doctest: +NORMALIZE_WHITESPACE
    --- Original        2005-01-26 23:30:50
    +++ Current         2010-04-02 10:20:52
    @@ -1,4 +1,4 @@
    +zero
     one
    -two
    -three
    +tree
     four
    """
    if sequencematcher is None:
        sequencematcher = difflib.SequenceMatcher

    function_lines = []
    if function_regexp:
        function_regexp = re.compile(function_regexp)
        function_lines = [k for k, line in enumerate(a) if function_regexp.match(line)]
        current_function = 0

    started = False
    for group in sequencematcher(None,a,b).get_grouped_opcodes(n):
        if not started:
            started = True
            fromdate = '\t{}'.format(fromfiledate) if fromfiledate else ''
            todate = '\t{}'.format(tofiledate) if tofiledate else ''
            yield '--- {}{}{}'.format(fromfile, fromdate, lineterm)
            yield '+++ {}{}{}'.format(tofile, todate, lineterm)

        first, last = group[0], group[-1]
        file1_range = _format_range_unified(first[1], last[2])
        file2_range = _format_range_unified(first[3], last[4])
        if function_lines:
            while current_function < len(function_lines) and function_lines[current_function] < first[1] + n:
                current_function += 1
            if current_function > 0:
                function = ' ' + a[function_lines[current_function - 1]].rstrip()
            else:
                function = ''
        else:
            function = ''
        yield '@@ -{} +{} @@{}{}'.format(file1_range, file2_range, function, lineterm)

        for tag, i1, i2, j1, j2 in group:
            if tag == 'equal':
                for line in a[i1:i2]:
                    yield ' ' + line
                continue
            if tag in ('replace', 'delete'):
                for line in a[i1:i2]:
                    yield '-' + line
            if tag in ('replace', 'insert'):
                for line in b[j1:j2]:
                    yield '+' + line


def unified_diff_files(a, b, sequencematcher=None, displaynames=None):
    """Generate the diff for two files.
    """
    # Should this actually be an error?
    if a == b:
        return []

    if displaynames:
        aname = displaynames[0]
        bname = displaynames[1]
    else:
        aname = a
        bname = b

    if a == '-':
        file_a = sys.stdin
        time_a = time.time()
    else:
        file_a = open(a, 'r')
        time_a = os.stat(a).st_mtime

    if b == '-':
        file_b = sys.stdin
        time_b = time.time()
    else:
        file_b = open(b, 'r')
        time_b = os.stat(b).st_mtime

    # TODO: Include fromfiledate and tofiledate if displaynames is not set
    return unified_diff(file_a.readlines(), file_b.readlines(),
                        fromfile=aname, tofile=bname,
                        sequencematcher=sequencematcher)

from patiencediff import (
    unique_lcs,
    recurse_matches,
    PatienceSequenceMatcher
    )

from klondikediff import KlondikeSequenceMatcher

import colordiff

def main(args):
    import optparse
    default_matcher = 'patience'
    if os.path.split(sys.argv[0])[1].startswith('klondi'):
        default_matcher = 'klondike'
    p = optparse.OptionParser(usage='%prog [options] file_a file_b'
                                    '\nFiles can be "-" to read from stdin')
    p.add_option('--patience', dest='matcher', action='store_const', const='patience',
                 default=default_matcher, help='Use the patience difference algorithm')
    p.add_option('--difflib', dest='matcher', action='store_const', const='difflib',
                 default=default_matcher, help='Use python\'s difflib algorithm')
    p.add_option('--klondike', dest='matcher', action='store_const', const='klondike',
                 default=default_matcher, help='Use the klondike diff algorithm')
    # TODO: implement more command line options
    #p.add_option('--unified', '-u', help='output NUM (default 3) lines of unified context')
    #p.add_option('--show-function-line', '-F', help='show the most recent line matching RE')
    #p.add_option('--color', '-c')

    algorithms = {'patience':PatienceSequenceMatcher, 'difflib':difflib.SequenceMatcher, 'klondike':KlondikeSequenceMatcher,}

    (opts, args) = p.parse_args(args)
    matcher = algorithms[opts.matcher]

    colordiff_writer = colordiff.DiffWriter(sys.stdout, color='always')
    def print_color(type, line):
        colordiff_writer.target.writelines(colordiff_writer.colorstring(type, line) + '\n')

    # check for git external diff syntax
    # TODO: check if git header is correct, old/new mode isn't handled
    displaynames = None
    if len(args) == 7:
        displaynames = ['a/' + args[0], 'b/' + args[0]]
        print_color('metaline', 'diff --git {0} {1}'.format(*displaynames))
        if '/dev/null' == args[1]:
            print_color('metaline', 'new file mode ' + args[6])
            args[2] = '0000000'
            args[3] = ''
            displaynames[0] = '/dev/null'
        if '/dev/null' == args[4]:
            print_color('metaline', 'deleted file mode ' + args[3])
            args[5] = '0000000'
            args[3] = ''
            displaynames[1] = '/dev/null'
        print_color('metaline', 'index {0}..{1} {2}'.format(args[2][:7], args[5][:7], args[3]))
        args = [args[1], args[4]]
    # git undocumented 9 parameter rename syntax (with git diff -M)
    elif len(args) == 9:
        displaynames = ['a/' + args[0], 'b/' + args[7]]
        print_color('metaline', 'diff --git {0} {1}'.format(*displaynames))
        print_color('metaline', args[8].strip())
        args = [args[1], args[4]]

    if len(args) != 2:
        print('You must supply 2 filenames')
        return -1

    # check for binary files
    result = binary_test(args[0], args[1])
    if 'binary_same' == result:
        return 0
    elif 'binary_different' == result:
        print('Binary files %s and %s differ' % (args[0], args[1]))
        return 2

    for line in unified_diff_files(args[0], args[1], sequencematcher=matcher, displaynames=displaynames):
        if line.endswith('\n'):
            colordiff_writer.writeline(line)
        else:
            # line including warning is seen as one line, even though it's printed on two lines
            colordiff_writer.writeline(line + '\n\\ No newline at end of file\n')
    # colordiff_writer keeps changed lines in buffer to compare, flush them when done
    colordiff_writer.flush()


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
