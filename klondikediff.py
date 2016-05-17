#!/usr/bin/env python
# Copyright (C) 2016 Piers Titus van der Torren
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

from __future__ import absolute_import

from bisect import bisect
import difflib
import re

# function copied from Bram Cohen's Patience diff from bzr
def unique_lcs_py(a, b):
    """Find the longest common subset for unique lines.

    :param a: An indexable object (such as string or list of strings)
    :param b: Another indexable object (such as string or list of strings)
    :return: A list of tuples, one for each line which is matched.
            [(line_in_a, line_in_b), ...]

    This only matches lines which are unique on both sides.
    This helps prevent common lines from over influencing match
    results.
    The longest common subset uses the Patience Sorting algorithm:
    http://en.wikipedia.org/wiki/Patience_sorting
    """
    # set index[line in a] = position of line in a unless
    # a is a duplicate, in which case it's set to None
    index = {}
    for i in xrange(len(a)):
        line = a[i]
        if line in index:
            index[line] = None
        else:
            index[line]= i
    # make btoa[i] = position of line i in a, unless
    # that line doesn't occur exactly once in both,
    # in which case it's set to None
    btoa = [None] * len(b)
    index2 = {}
    for pos, line in enumerate(b):
        next = index.get(line)
        if next is not None:
            if line in index2:
                # unset the previous mapping, which we now know to
                # be invalid because the line isn't unique
                btoa[index2[line]] = None
                del index[line]
            else:
                index2[line] = pos
                btoa[pos] = next
    # this is the Patience sorting algorithm
    # see http://en.wikipedia.org/wiki/Patience_sorting
    backpointers = [None] * len(b)
    stacks = []
    lasts = []
    k = 0
    for bpos, apos in enumerate(btoa):
        if apos is None:
            continue
        # as an optimization, check if the next line comes at the end,
        # because it usually does
        if stacks and stacks[-1] < apos:
            k = len(stacks)
        # as an optimization, check if the next line comes right after
        # the previous line, because usually it does
        elif stacks and stacks[k] < apos and (k == len(stacks) - 1 or
                                              stacks[k+1] > apos):
            k += 1
        else:
            k = bisect(stacks, apos)
        if k > 0:
            backpointers[bpos] = lasts[k-1]
        if k < len(stacks):
            stacks[k] = apos
            lasts[k] = bpos
        else:
            stacks.append(apos)
            lasts.append(bpos)
    if len(lasts) == 0:
        return []
    result = []
    k = lasts[-1]
    while k is not None:
        result.append((btoa[k], k))
        k = backpointers[k]
    result.reverse()
    return result


def _check_consistency(answer):
    # For consistency sake, make sure all matches are only increasing
    next_a = -1
    next_b = -1
    for (a, b, match_len) in answer:
        if a < next_a:
            raise ValueError('Non increasing matches for a')
        if b < next_b:
            raise ValueError('Non increasing matches for b')
        next_a = a + match_len
        next_b = b + match_len


class KlondikeSequenceMatcher(difflib.SequenceMatcher):
    """Compare a pair of sequences using longest common subset."""

    _do_check_consistency = True

    def __init__(self, isjunk=None, a='', b='', extra_effort=1):
        if isjunk is not None:
            raise NotImplementedError('Currently we do not support'
                                      ' isjunk for sequence matching')
        difflib.SequenceMatcher.__init__(self, isjunk, a, b)
        self.extra_effort = extra_effort

    def get_matching_blocks(self):
        """Return list of triples describing matching subsequences.

        In this algorithm blocks are considered matching when there are changes
        in junk, which is defined as whitespace or 3+ repeating characters.

        This function currently only supports lists of strings, for single string
        diff difflib is better suited.

        Each triple is of the form (i, j, n), and means that
        a[i:i+n] == b[j:j+n].  The triples are monotonically increasing in
        i and in j.

        The last triple is a dummy, (len(a), len(b), 0), and is the only
        triple with n==0.

        >>> s = KlondikeSequenceMatcher(None, "abxcd", "abcd")
        >>> s.get_matching_blocks()
        [(0, 0, 2), (3, 2, 2), (5, 4, 0)]
        """

        if self.matching_blocks is not None:
            return self.matching_blocks

        # remove whitespace and repeated characters
        clear_junk = re.compile(r'(.)\1*(?=\1{2})|[ \t\r\n]*')
        self.a_ws = a_ws = [clear_junk.sub('', s) for s in self.a]
        self.b_ws = b_ws = [clear_junk.sub('', s) for s in self.b]
        #a_ws = [s.strip().replace(' ','').replace('\t','') for s in self.a]
        #b_ws = [s.strip().replace(' ','').replace('\t','') for s in self.b]
        # TODO: more junk stripping?

        # first match blocks at beginning and end of file
        start_line = 0;
        while a_ws[start_line] == b_ws[start_line]:
            start_line += 1
        end_line = -1
        while a_ws[end_line] == b_ws[end_line]:
            end_line -= 1
        end_line += 1
        if end_line == 0:
            # use None for slicing till the end
            end_line = None

        # in the rest find LCS of unique lines
        result = unique_lcs_py(a_ws[start_line:end_line], b_ws[start_line:end_line])
        result = [(apos + start_line, bpos + start_line) for apos, bpos in result]

        # grow unique matches with surrounding lines
        matches = []
        if start_line:
            matches.append((0, 0, start_line))
        last_a = last_b = start_line
        for apos, bpos in result:
            # if previous match overlaps current just skip it.
            # Only a is checked because lines are unique anyway
            # TODO: check if <= is correct, print((apos-last_a,bpos-last_b))
            if apos <= last_a:
                continue
            start = -1
            while a_ws[apos + start] == b_ws[bpos + start]:
                start -= 1
            start += 1
            end = 1
            while a_ws[apos + end] == b_ws[bpos + end]:
                end += 1

            # Search for additional matches which might not have been found due to not unique lines
            # Use difflib here, as unique_lcs was not successfull this give better chances
            if apos + start > last_a and bpos + start > last_b and apos + bpos + 2 * start > last_a + last_b + 2:
                in_matches = difflib.SequenceMatcher(None, a_ws[last_a:apos+start], b_ws[last_b:bpos+start]).get_matching_blocks()
                matches.extend([(a+last_a, b+last_b, s) for a,b,s in in_matches if s])

            matches.append((apos + start, bpos + start, end - start))
            last_a = apos + end
            last_b = bpos + end

        if end_line != None:
            matches.append( (len(a_ws) + end_line, len(b_ws) + end_line, -end_line) )

        # add dummy tuple
        matches.append( (len(a_ws), len(b_ws), 0) )

        # check for same lines before and after change
        for n, (apos, bpos, size) in enumerate(matches[:-1]):
            d = max(apos + size - matches[n+1][0], bpos + size - matches[n+1][1])
            if d > 0:
                for k in range(d): # shift change to go untill empty line, if possible
                    if a_ws[matches[n+1][0] + d - k - 1] == '':
                        matches[n] = (matches[n][0], matches[n][1], matches[n][2] - k)
                        d -= k
                        break;
                matches[n+1] = (matches[n+1][0] + d, matches[n+1][1] + d, matches[n+1][2] - d)

        self.matching_blocks = matches

        if KlondikeSequenceMatcher._do_check_consistency:
            if __debug__:
                _check_consistency(self.matching_blocks)

        return self.matching_blocks

    def get_opcodes(self):
        """Return list of 5-tuples describing how to turn a into b.

        Each tuple is of the form (tag, i1, i2, j1, j2).  The first tuple
        has i1 == j1 == 0, and remaining tuples have i1 == the i2 from the
        tuple preceding it, and likewise for j1 == the previous j2.

        The tags are strings, with these meanings:

        'replace':  a[i1:i2] should be replaced by b[j1:j2]
        'delete':   a[i1:i2] should be deleted.
                    Note that j1==j2 in this case.
        'insert':   b[j1:j2] should be inserted at a[i1:i1].
                    Note that i1==i2 in this case.
        'equal':    a[i1:i2] == b[j1:j2]

        >>> a = "qabxcd"
        >>> b = "abycdf"
        >>> s = SequenceMatcher(None, a, b)
        >>> for tag, i1, i2, j1, j2 in s.get_opcodes():
        ...    print ("%7s a[%d:%d] (%s) b[%d:%d] (%s)" %
        ...           (tag, i1, i2, a[i1:i2], j1, j2, b[j1:j2]))
         delete a[0:1] (q) b[0:0] ()
          equal a[1:3] (ab) b[0:2] (ab)
        replace a[3:4] (x) b[2:3] (y)
          equal a[4:6] (cd) b[3:5] (cd)
         insert a[6:6] () b[5:6] (f)
        """

        if self.opcodes is not None:
            return self.opcodes

        def add_tag(t):
            tag = 'replace'
            if t[0] == t[1]:
                tag = 'insert'
            elif t[2] == t[3]:
                tag = 'delete'
            return (tag,) + t
        i = j = 0
        self.opcodes = answer = []
        for ai, bj, size in self.get_matching_blocks():

            # invariant:  we've pumped out correct diffs to change
            # a[:i] into b[:j], and the next matching block is
            # a[ai:ai+size] == b[bj:bj+size].  So we need to pump
            # out a diff to change a[i:ai] into b[j:bj], pump out
            # the matching block, and move (i,j) beyond the match
            tag = ''
            if i < ai and j < bj:
                tag = 'replace'
                # find changed lines and separate them from replaced blocks
                # TODO: handling of split or combined lines could be improved
                # TODO: difflib seems to mess up sometimes, like with these lines
                if self.extra_effort and (i < ai - 1 or j < bj - 1):
                    a = 'a\n'.join(self.a_ws[i:ai])
                    b = 'b\n'.join(self.b_ws[j:bj])
                    cur_a = cur_b = 0
                    cur_an = cur_bn = 0
                    prev_an = prev_bn = 0
                    matches = difflib.SequenceMatcher(None, a, b).get_matching_blocks()
                    for m in matches:
                        if m[2] >= 5: # only act when matches of at least 5 chars found
                            while cur_a <= m[0]:
                                cur_a += len(self.a_ws[i+cur_an]) + 2
                                cur_an += 1
                            while cur_b <= m[1]:
                                cur_b += len(self.b_ws[j+cur_bn]) + 2
                                cur_bn += 1
                            if prev_an < cur_an and prev_bn < cur_bn:
                                if prev_an < cur_an - 1 or prev_bn < cur_bn - 1:
                                    answer.append( add_tag((
                                        i + prev_an, i + cur_an - 1,
                                        j + prev_bn, j + cur_bn - 1 )) )
                                # extra check if replaced lines are equal, sometimes happens somehow
                                if self.a[i + cur_an - 1] == self.b[j + cur_bn - 1]:
                                    print 'why missed by Patiencediff and Difflib?'
                                    print self.a[i + cur_an - 1]
                                    tag = 'equal'
                                else:
                                    tag = 'replace'
                                answer.append( (tag,
                                    i + cur_an - 1, i + cur_an,
                                    j + cur_bn - 1, j + cur_bn) )
                                prev_an, prev_bn = cur_an, cur_bn

                    if i + prev_an < ai or j + prev_bn < bj:
                        answer.append( add_tag((
                            i + prev_an, ai,
                            j + prev_bn, bj)) )
                    tag = ''
            elif i < ai:
                tag = 'delete'
            elif j < bj:
                tag = 'insert'
            if tag:
                answer.append( (tag, i, ai, j, bj) )
            i, j = ai+size, bj+size

            # check matches for junk changes
            n1 = 0
            for n in range(size):
                if self.a[ai + n] != self.b[bj + n]:
                    if n1 < n:
                        answer.append( ('equal', ai + n1, ai + n, bj + n1, bj + n) )
                    n1 = n + 1
                    answer.append( ('replace', ai + n, ai + n + 1, bj + n, bj + n + 1) )
            if n1 < size:
                answer.append( ('equal', ai + n1, ai + size, bj + n1, bj + size) )

        # sanity check if both documents are fully covered
        errors = []
        i3 = j3 = 0
        for t, i1, i2, j1, j2 in answer:
            if not (i1 == i3 and j1 == j3):
                errors.append("{} should be {}".format((t, i1, i2, j1, j2), (i3,j3)))
            i3, j3 = i2, j2
        if not (i3 == len(self.a) and j3 == len(self.b)):
            errors.append("{} should end on {}".format((t, i1, i2, j1, j2), (len(self.a), len(self.b))))
        if errors:
            errors.append("Error in algorithm, please report")
            raise Exception('\n'.join(errors))

        return answer
