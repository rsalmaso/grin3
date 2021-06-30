# Copyright (C) 2017-2021, Raffaele Salmaso <raffaele@salmaso.org>
# Copyright (C) 2007, Enthought, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#  * Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#  * Neither the name of Enthought, Inc. nor the names of its contributors may
#    be used to endorse or promote products derived from this software without
#    specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import re
from io import BytesIO
from unittest import TestCase

import grin

all_foo = b"""foo
foo
foo
foo
foo
"""
first_foo = b"""foo
bar
bar
bar
bar
"""
last_foo = b"""bar
bar
bar
bar
foo
"""
second_foo = b"""bar
foo
bar
bar
bar
"""
second_last_foo = b"""bar
bar
bar
foo
bar
"""
middle_foo = b"""bar
bar
foo
bar
bar
"""
small_gap = b"""bar
bar
foo
bar
foo
bar
bar
"""
no_eol = b"foo"
middle_of_line = b"""bar
bar
barfoobar
bar
bar
"""
utf_8_foo = "Rémy\n".encode("utf8")
latin_1_foo = "Rémy\n".encode("latin1")
regex_metachar_foo = b"""bar
bar
def foo(...):
bar
foo
bar
bar
"""
unicode_digits = b"""This contains
an Arabic-Indic digit \xd9\xa2 on the
second line.
"""


class GrepTestCase(TestCase):
    def test_non_ascii(self):
        non_ascii = grin.GrepText(re.compile("é"))
        self.assertEqual(
            non_ascii.do_grep(BytesIO(utf_8_foo), encoding="utf8"),
            [(0, 0, "Rémy\n", [(1, 2)])],
        )
        self.assertEqual(
            non_ascii.do_grep(BytesIO(latin_1_foo), encoding="latin1"),
            [(0, 0, "Rémy\n", [(1, 2)])],
        )

        self.assertEqual(non_ascii.do_grep(BytesIO(utf_8_foo), encoding="latin1"), [])

        # Fallback to latin1
        self.assertEqual(
            non_ascii.do_grep(BytesIO(latin_1_foo), encoding="utf8"),
            [(0, 0, "Rémy\n", [(1, 2)])],
        )

    def test_basic_defaults(self):
        # Test the basic defaults, no context.
        gt_default = grin.GrepText(re.compile("foo"))
        self.assertEqual(
            gt_default.do_grep(BytesIO(all_foo)),
            [
                (0, 0, "foo\n", [(0, 3)]),
                (1, 0, "foo\n", [(0, 3)]),
                (2, 0, "foo\n", [(0, 3)]),
                (3, 0, "foo\n", [(0, 3)]),
                (4, 0, "foo\n", [(0, 3)]),
            ],
        )
        self.assertEqual(gt_default.do_grep(BytesIO(first_foo)), [(0, 0, "foo\n", [(0, 3)])])
        self.assertEqual(gt_default.do_grep(BytesIO(last_foo)), [(4, 0, "foo\n", [(0, 3)])])
        self.assertEqual(gt_default.do_grep(BytesIO(second_foo)), [(1, 0, "foo\n", [(0, 3)])])
        self.assertEqual(gt_default.do_grep(BytesIO(second_last_foo)), [(3, 0, "foo\n", [(0, 3)])])
        self.assertEqual(gt_default.do_grep(BytesIO(middle_foo)), [(2, 0, "foo\n", [(0, 3)])])
        self.assertEqual(
            gt_default.do_grep(BytesIO(small_gap)),
            [(2, 0, "foo\n", [(0, 3)]), (4, 0, "foo\n", [(0, 3)])],
        )
        self.assertEqual(gt_default.do_grep(BytesIO(no_eol)), [(0, 0, "foo", [(0, 3)])])
        self.assertEqual(
            gt_default.do_grep(BytesIO(middle_of_line)),
            [(2, 0, "barfoobar\n", [(3, 6)])],
        )

    def test_symmetric_one_line_context(self):
        # Symmetric 1-line context.

        gt_context_1 = grin.GrepText(re.compile("foo"), options=grin.Options(before_context=1, after_context=1))
        self.assertEqual(
            gt_context_1.do_grep(BytesIO(all_foo)),
            [
                (0, 0, "foo\n", [(0, 3)]),
                (1, 0, "foo\n", [(0, 3)]),
                (2, 0, "foo\n", [(0, 3)]),
                (3, 0, "foo\n", [(0, 3)]),
                (4, 0, "foo\n", [(0, 3)]),
            ],
        )
        self.assertEqual(
            gt_context_1.do_grep(BytesIO(first_foo)),
            [(0, 0, "foo\n", [(0, 3)]), (1, 1, "bar\n", None)],
            # [(1, 0, "foo\n", [(0, 3)]), (2, 1, "bar\n", None)],
        )
        self.assertEqual(
            gt_context_1.do_grep(BytesIO(last_foo)),
            [(3, -1, "bar\n", None), (4, 0, "foo\n", [(0, 3)])],
            # [(4, -1, "bar\n", None), (5, 0, "foo\n", [(0, 3)])],
        )
        self.assertEqual(
            gt_context_1.do_grep(BytesIO(second_foo)),
            [(0, -1, "bar\n", None), (1, 0, "foo\n", [(0, 3)]), (2, 1, "bar\n", None)],
            # [(1, -1, "bar\n", None), (2, 0, "foo\n", [(0, 3)]), (3, 1, "bar\n", None)],
        )
        self.assertEqual(
            gt_context_1.do_grep(BytesIO(second_last_foo)),
            [(2, -1, "bar\n", None), (3, 0, "foo\n", [(0, 3)]), (4, 1, "bar\n", None)],
            # [(3, -1, "bar\n", None), (4, 0, "foo\n", [(0, 3)]), (5, 1, "bar\n", None)],
        )
        self.assertEqual(
            gt_context_1.do_grep(BytesIO(middle_foo)),
            [(1, -1, "bar\n", None), (2, 0, "foo\n", [(0, 3)]), (3, 1, "bar\n", None)],
            # [(2, -1, "bar\n", None), (3, 0, "foo\n", [(0, 3)]), (4, 1, "bar\n", None)],
        )
        self.assertEqual(
            gt_context_1.do_grep(BytesIO(small_gap)),
            [
                (1, -1, "bar\n", None),
                (2, 0, "foo\n", [(0, 3)]),
                (3, 1, "bar\n", None),
                (4, 0, "foo\n", [(0, 3)]),
                (5, 1, "bar\n", None),
            ],
        )
        self.assertEqual(gt_context_1.do_grep(BytesIO(no_eol)), [(0, 0, "foo", [(0, 3)])])
        self.assertEqual(
            gt_context_1.do_grep(BytesIO(middle_of_line)),
            [(1, -1, "bar\n", None), (2, 0, "barfoobar\n", [(3, 6)]), (3, 1, "bar\n", None)],
        )

    def test_symmetric_two_line_context(self):
        # Symmetric 2-line context.

        gt_context_2 = grin.GrepText(re.compile("foo"), options=grin.Options(before_context=2, after_context=2))
        self.assertEqual(
            gt_context_2.do_grep(BytesIO(all_foo)),
            [
                (0, 0, "foo\n", [(0, 3)]),
                (1, 0, "foo\n", [(0, 3)]),
                (2, 0, "foo\n", [(0, 3)]),
                (3, 0, "foo\n", [(0, 3)]),
                (4, 0, "foo\n", [(0, 3)]),
            ],
        )
        self.assertEqual(
            gt_context_2.do_grep(BytesIO(first_foo)),
            [(0, 0, "foo\n", [(0, 3)]), (1, 1, "bar\n", None), (2, 1, "bar\n", None)],
        )
        self.assertEqual(
            gt_context_2.do_grep(BytesIO(last_foo)),
            [(2, -1, "bar\n", None), (3, -1, "bar\n", None), (4, 0, "foo\n", [(0, 3)])],
        )
        self.assertEqual(
            gt_context_2.do_grep(BytesIO(second_foo)),
            [(0, -1, "bar\n", None), (1, 0, "foo\n", [(0, 3)]), (2, 1, "bar\n", None), (3, 1, "bar\n", None)],
        )
        self.assertEqual(
            gt_context_2.do_grep(BytesIO(second_last_foo)),
            [(1, -1, "bar\n", None), (2, -1, "bar\n", None), (3, 0, "foo\n", [(0, 3)]), (4, 1, "bar\n", None)],
        )
        self.assertEqual(
            gt_context_2.do_grep(BytesIO(middle_foo)),
            [
                (0, -1, "bar\n", None),
                (1, -1, "bar\n", None),
                (2, 0, "foo\n", [(0, 3)]),
                (3, 1, "bar\n", None),
                (4, 1, "bar\n", None),
            ],
        )
        self.assertEqual(
            gt_context_2.do_grep(BytesIO(small_gap)),
            [
                (0, -1, "bar\n", None),
                (1, -1, "bar\n", None),
                (2, 0, "foo\n", [(0, 3)]),
                (3, 1, "bar\n", None),
                (4, 0, "foo\n", [(0, 3)]),
                (5, 1, "bar\n", None),
                (6, 1, "bar\n", None),
            ],
        )
        self.assertEqual(gt_context_2.do_grep(BytesIO(no_eol)), [(0, 0, "foo", [(0, 3)])])
        self.assertEqual(
            gt_context_2.do_grep(BytesIO(middle_of_line)),
            [
                (0, -1, "bar\n", None),
                (1, -1, "bar\n", None),
                (2, 0, "barfoobar\n", [(3, 6)]),
                (3, 1, "bar\n", None),
                (4, 1, "bar\n", None),
            ],
        )

    def test_one_line_before_no_lines_after(self):
        # 1 line of before-context, no lines after.

        gt_before_context_1 = grin.GrepText(re.compile("foo"), options=grin.Options(before_context=1, after_context=0))
        self.assertEqual(
            gt_before_context_1.do_grep(BytesIO(all_foo)),
            [
                (0, 0, "foo\n", [(0, 3)]),
                (1, 0, "foo\n", [(0, 3)]),
                (2, 0, "foo\n", [(0, 3)]),
                (3, 0, "foo\n", [(0, 3)]),
                (4, 0, "foo\n", [(0, 3)]),
            ],
        )
        self.assertEqual(gt_before_context_1.do_grep(BytesIO(first_foo)), [(0, 0, "foo\n", [(0, 3)])])
        self.assertEqual(
            gt_before_context_1.do_grep(BytesIO(last_foo)),
            [(3, -1, "bar\n", None), (4, 0, "foo\n", [(0, 3)])],
        )
        self.assertEqual(
            gt_before_context_1.do_grep(BytesIO(second_foo)),
            [(0, -1, "bar\n", None), (1, 0, "foo\n", [(0, 3)])],
        )
        self.assertEqual(
            gt_before_context_1.do_grep(BytesIO(second_last_foo)),
            [(2, -1, "bar\n", None), (3, 0, "foo\n", [(0, 3)])],
        )
        self.assertEqual(
            gt_before_context_1.do_grep(BytesIO(middle_foo)),
            [(1, -1, "bar\n", None), (2, 0, "foo\n", [(0, 3)])],
        )
        self.assertEqual(
            gt_before_context_1.do_grep(BytesIO(small_gap)),
            [(1, -1, "bar\n", None), (2, 0, "foo\n", [(0, 3)]), (3, -1, "bar\n", None), (4, 0, "foo\n", [(0, 3)])],
        )
        self.assertEqual(gt_before_context_1.do_grep(BytesIO(no_eol)), [(0, 0, "foo", [(0, 3)])])
        self.assertEqual(
            gt_before_context_1.do_grep(BytesIO(middle_of_line)),
            [(1, -1, "bar\n", None), (2, 0, "barfoobar\n", [(3, 6)])],
        )

    def test_one_line_after_context_no_lines_before(self):
        # 1 line of after-context, no lines before.

        gt_after_context_1 = grin.GrepText(re.compile("foo"), options=grin.Options(before_context=0, after_context=1))
        self.assertEqual(
            gt_after_context_1.do_grep(BytesIO(all_foo)),
            [
                (0, 0, "foo\n", [(0, 3)]),
                (1, 0, "foo\n", [(0, 3)]),
                (2, 0, "foo\n", [(0, 3)]),
                (3, 0, "foo\n", [(0, 3)]),
                (4, 0, "foo\n", [(0, 3)]),
            ],
        )
        self.assertEqual(
            gt_after_context_1.do_grep(BytesIO(first_foo)),
            [(0, 0, "foo\n", [(0, 3)]), (1, 1, "bar\n", None)],
        )
        self.assertEqual(gt_after_context_1.do_grep(BytesIO(last_foo)), [(4, 0, "foo\n", [(0, 3)])])
        self.assertEqual(
            gt_after_context_1.do_grep(BytesIO(second_foo)),
            [(1, 0, "foo\n", [(0, 3)]), (2, 1, "bar\n", None)],
        )
        self.assertEqual(
            gt_after_context_1.do_grep(BytesIO(second_last_foo)),
            [(3, 0, "foo\n", [(0, 3)]), (4, 1, "bar\n", None)],
        )
        self.assertEqual(
            gt_after_context_1.do_grep(BytesIO(middle_foo)),
            [(2, 0, "foo\n", [(0, 3)]), (3, 1, "bar\n", None)],
        )
        self.assertEqual(
            gt_after_context_1.do_grep(BytesIO(small_gap)),
            [(2, 0, "foo\n", [(0, 3)]), (3, 1, "bar\n", None), (4, 0, "foo\n", [(0, 3)]), (5, 1, "bar\n", None)],
        )
        self.assertEqual(gt_after_context_1.do_grep(BytesIO(no_eol)), [(0, 0, "foo", [(0, 3)])])
        self.assertEqual(
            gt_after_context_1.do_grep(BytesIO(middle_of_line)),
            [(2, 0, "barfoobar\n", [(3, 6)]), (3, 1, "bar\n", None)],
        )

    def test_fixed_string_option(self):
        # -F/--fixed-string works with unescaped regex metachars

        options = grin.Options(fixed_string=True, regex="foo(", re_flags=[], before_context=0, after_context=0)
        regex_with_metachars = grin.GrepText(grin.utils.get_regex(options))
        self.assertEqual(
            regex_with_metachars.do_grep(BytesIO(regex_metachar_foo)),
            [(2, 0, "def foo(...):\n", [(4, 8)])],
        )

    def test_ascii(self):
        # -a/--ascii

        # No match when in ascii mode
        options = grin.Options(regex=r"\d", re_flags=[re.A], before_context=0, after_context=0)
        regex_unicode = grin.GrepText(grin.utils.get_regex(options))
        self.assertEqual(
            regex_unicode.do_grep(BytesIO(unicode_digits)),
            [],
        )
        # [(1, 0, 'an Arabic-Indic digit ٢ on the\n', [(22, 23)])]

        # Unicode (default)
        options = grin.Options(regex=r"\d", re_flags=[], before_context=0, after_context=0)
        regex_unicode = grin.GrepText(grin.utils.get_regex(options))
        self.assertEqual(
            regex_unicode.do_grep(BytesIO(unicode_digits)),
            [(1, 0, 'an Arabic-Indic digit ٢ on the\n', [(22, 23)])],
        )
