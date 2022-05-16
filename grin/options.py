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

__all__ = ["Options"]


class Options(dict):
    """Simple options."""

    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self.setdefault("before_context", 0)
        self.setdefault("after_context", 0)
        self.setdefault("show_line_numbers", True)
        self.setdefault("show_match", True)
        self.setdefault("show_filename", True)
        self.setdefault("show_emacs", False)
        self.setdefault("skip_hidden_dirs", False)
        self.setdefault("skip_backup_files", True)
        self.setdefault("skip_hidden_files", False)
        self.setdefault("skip_dirs", set())
        self.setdefault("skip_exts", set())
        self.setdefault("skip_symlink_dirs", True)
        self.setdefault("skip_symlink_files", True)
        self.setdefault("binary_bytes", 4096)
        self.setdefault("re_flags", [])
        self.setdefault("fixed_string", False)
        self.setdefault("word_regexp", False)
        self.__dict__ = self
