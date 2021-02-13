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

__all__ = ["get_line_offsets", "get_regex", "is_binary_string", "to_str"]


# Use file(1)'s choices for what's text and what's not.
TEXTCHARS = bytes([7, 8, 9, 10, 12, 13, 27] + list(range(0x20, 0x100)))
ALLBYTES = bytes(range(256))


def to_str(s, encoding="utf8"):
    if isinstance(s, str):
        return s
    try:
        return s.decode(encoding)
    except UnicodeDecodeError:
        return s.decode("latin1")


def is_binary_string(bytes):
    """Determine if a string is classified as binary rather than text.

    Parameters
    ----------
    bytes : str

    Returns
    -------
    is_binary : bool
    """
    nontext = bytes.translate(ALLBYTES, TEXTCHARS)
    return bool(nontext)


def get_line_offsets(block):
    """Compute the list of offsets in DataBlock 'block' which correspond to
    the beginnings of new lines.

    Returns: (offset list, count of lines in "current block")
    """
    # Note: this implementation based on string.find() benchmarks about twice as
    # fast as a list comprehension using re.finditer().
    line_offsets = [0]
    line_count = 0  # Count of lines inside range [block.start, block.end) *only*
    s = block.data
    while True:
        next_newline = s.find("\n", line_offsets[-1])
        if next_newline < 0:
            # Tack on a final "line start" corresponding to EOF, if not done already.
            # This makes it possible to determine the length of each line by computing
            # a difference between successive elements.
            if line_offsets[-1] < len(s):
                line_offsets.append(len(s))
            return (line_offsets, line_count)
        else:
            line_offsets.append(next_newline + 1)
            # Keep track of the count of lines within the "current block"
            if next_newline >= block.start and next_newline < block.end:
                line_count += 1


def get_regex(args):
    """Get the compiled regex object to search with."""
    # Combine all of the flags.
    flags = 0
    for flag in args.re_flags:
        flags |= flag
    pattern = re.escape(args.regex) if args.fixed_string else args.regex
    return re.compile(pattern, flags)
