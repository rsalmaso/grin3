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

import fnmatch
import gzip
import os
import stat

from .utils import is_binary_string

__all__ = ["FileRecognizer", "get_recognizer"]

# gzip magic header bytes.
GZIP_MAGIC = b"\037\213"


class FileRecognizer:
    """Configurable way to determine what kind of file something is.

    Attributes
    ----------
    skip_hidden_dirs : bool
        Whether to skip recursing into hidden directories, i.e. those starting
        with a "." character.
    skip_hidden_files : bool
        Whether to skip hidden files.
    skip_backup_files : bool
        Whether to skip backup files.
    skip_dirs : container of str
        A list of directory names to skip. For example, one might want to skip
        directories named "CVS".
    skip_exts : container of str
        A list of file extensions to skip. For example, some file names like
        ".so" are known to be binary and one may want to always skip them.
    skip_symlink_dirs : bool
        Whether to skip symlinked directories.
    skip_symlink_files : bool
        Whether to skip symlinked files.
    binary_bytes : int
        The number of bytes to check at the beginning and end of a file for
        binary characters.
    include : Optional[str]
        fnmatch pattern to match file names against
    """

    def __init__(
        self,
        skip_hidden_dirs=False,
        skip_hidden_files=False,
        skip_backup_files=False,
        skip_dirs=set(),
        skip_exts=set(),
        skip_symlink_dirs=True,
        skip_symlink_files=True,
        binary_bytes=4096,
        include=None,
    ):
        self.skip_hidden_dirs = skip_hidden_dirs
        self.skip_hidden_files = skip_hidden_files
        self.skip_backup_files = skip_backup_files
        self.skip_dirs = skip_dirs

        # For speed, split extensions into the simple ones, that are
        # compatible with os.path.splitext and hence can all be
        # checked for in a single set-lookup, and the weirdos that
        # can't and therefore must be checked for one at a time.
        self.skip_exts_simple = set()
        self.skip_exts_endswith = list()
        for ext in skip_exts:
            if os.path.splitext("foo.bar" + ext)[1] == ext:
                self.skip_exts_simple.add(ext)
            else:
                self.skip_exts_endswith.append(ext)

        self.skip_symlink_dirs = skip_symlink_dirs
        self.skip_symlink_files = skip_symlink_files
        self.binary_bytes = binary_bytes
        self.include = include

    def is_binary(self, filename):
        """Determine if a given file is binary or not.

        Parameters
        ----------
        filename : str

        Returns
        -------
        is_binary : bool
        """
        with open(filename, "rb") as fp:
            return self._is_binary_file(fp)

    def _is_binary_file(self, f):
        """Determine if a given filelike object has binary data or not.

        Parameters
        ----------
        f : filelike object

        Returns
        -------
        is_binary : bool
        """
        try:
            data = f.read(self.binary_bytes)
        except Exception:
            # When trying to read from something that looks like a gzipped file,
            # it may be corrupt. If we do get an error, assume that the file is binary.
            return True
        return is_binary_string(data)

    def is_gzipped_text(self, filename):
        """Determine if a given file is a gzip-compressed text file or not.

        If the uncompressed file is binary and not text, then this will return
        False.

        Parameters
        ----------
        filename : str

        Returns
        -------
        is_gzipped_text : bool
        """
        is_gzipped_text = False
        with open(filename, "rb") as fp:
            marker = fp.read(2)

        if marker == GZIP_MAGIC:
            with gzip.open(filename) as fp:
                try:
                    is_gzipped_text = not self._is_binary_file(fp)
                except IOError:
                    # We saw the GZIP_MAGIC marker, but it is not actually a gzip
                    # file.
                    is_gzipped_text = False
        return is_gzipped_text

    def recognize(self, filename, direntry):
        """Determine what kind of thing a filename represents.

        It will also determine what a directory walker should do with the
        file:

            'text' :
                It should should be grepped for the pattern and the matching
                lines displayed.
            'binary' :
                The file is binary and should be either ignored or grepped
                without displaying the matching lines depending on the
                configuration.
            'gzip' :
                The file is gzip-compressed and should be grepped while
                uncompressing.
            'directory' :
                The filename refers to a readable and executable directory that
                should be recursed into if we are configured to do so.
            'link' :
                The filename refers to a symlink that should be skipped.
            'unreadable' :
                The filename cannot be read (and also, in the case of
                directories, is not executable either).
            'skip' :
                The filename, whether a directory or a file, should be skipped
                for any other reason.

        Parameters
        ----------
        filename : str

        Returns
        -------
        kind : str
        """
        try:
            if direntry is None:
                st_mode = os.stat(filename).st_mode
                if stat.S_ISREG(st_mode):
                    return self.recognize_file(filename, None)
                elif stat.S_ISDIR(st_mode):
                    return self.recognize_directory(filename, None)
                else:
                    # We're only interested in regular files and directories.
                    # A named pipe in particular would be problematic, because
                    # it would cause open() to hang indefinitely.
                    return "skip"
            else:
                if direntry.is_file():
                    return self.recognize_file(filename, direntry)
                elif direntry.is_dir():
                    return self.recognize_directory(filename, direntry)
                else:
                    return "skip"
        except OSError:
            return "unreadable"

    def recognize_directory(self, filename, direntry):
        """Determine what to do with a directory."""
        basename = os.path.split(filename)[-1]
        if self.skip_hidden_dirs and basename.startswith(".") and basename not in (".", ".."):
            return "skip"
        if self.skip_symlink_dirs:
            if direntry is None:
                if os.path.islink(filename):
                    return "link"
            else:
                if direntry.is_symlink():
                    return "link"
        if basename in self.skip_dirs:
            return "skip"
        return "directory"

    def recognize_file(self, filename, direntry):
        """Determine what to do with a file."""
        basename = os.path.split(filename)[-1]
        if self.skip_hidden_files and basename.startswith("."):
            return "skip"
        if self.skip_backup_files and basename.endswith("~"):
            return "skip"
        if self.skip_symlink_files:
            if direntry is None:
                if os.path.islink(filename):
                    return "link"
            else:
                if direntry.is_symlink():
                    return "link"

        if self.include is not None:
            if not fnmatch.fnmatch(basename, self.include):
                return "skip"

        filename_nc = os.path.normcase(filename)
        ext = os.path.splitext(filename_nc)[1]
        if ext in self.skip_exts_simple or ext.startswith(".~"):
            return "skip"
        for ext in self.skip_exts_endswith:
            if filename_nc.endswith(ext):
                return "skip"
        try:
            if self.is_binary(filename):
                if self.is_gzipped_text(filename):
                    return "gzip"
                else:
                    return "binary"
            else:
                return "text"
        except (OSError, IOError):
            return "unreadable"

    def walk(self, startpath, direntry=None):
        """Walk the tree from a given start path yielding all of the files (not
        directories) and their kinds underneath it depth first.

        Paths which are recognized as 'skip', 'link', or 'unreadable' will
        simply be passed over without comment.

        Parameters
        ----------
        startpath : str

        Yields
        ------
        filename : str
        kind : str
        """
        kind = self.recognize(startpath, direntry)
        if kind in ("binary", "text", "gzip"):
            yield startpath, kind
            # Not a directory, so there is no need to recurse.
            return
        elif kind == "directory":
            try:
                entries = os.scandir(startpath)
            except OSError:
                return
            for entry in sorted(entries, key=lambda e: e.name):
                path = os.path.join(startpath, entry.name)
                for fn, k in self.walk(path, entry):
                    yield fn, k


def get_recognizer(args):
    """Get the file recognizer object from the configured options."""
    # Make sure we have empty sets when we have empty strings.
    skip_dirs = set([x for x in args.skip_dirs.split(",") if x])
    skip_exts = set([x for x in args.skip_exts.split(",") if x])
    fr = FileRecognizer(
        skip_hidden_files=args.skip_hidden_files,
        skip_backup_files=args.skip_backup_files,
        skip_hidden_dirs=args.skip_hidden_dirs,
        skip_dirs=skip_dirs,
        skip_exts=skip_exts,
        skip_symlink_files=not args.follow_symlinks,
        skip_symlink_dirs=not args.follow_symlinks,
        include=args.include,
    )
    return fr
