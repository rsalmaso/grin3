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

__all__ = ["DataBlock", "EMPTY_DATABLOCK"]


class DataBlock:
    """This class holds a block of data read from a file, along with
    some preceding and trailing context.

    Attributes
    ----------
    data  : byte string
    start : int
        Offset into 'data' where the "current block" begins; everything
        prior to this is 'before' context bytes
    end : int
        Offset into 'data' where the "current block" ends; everything
        after this is 'after' context bytes
    before_count : int
        Number of lines contained in data[:start]
    is_last : bool
        True if this is the final block in the file
    """

    def __init__(self, data="", start=0, end=0, before_count=0, is_last=False):
        self.data = data
        self.start = start
        self.end = end
        self.before_count = before_count
        self.is_last = is_last


EMPTY_DATABLOCK = DataBlock()
