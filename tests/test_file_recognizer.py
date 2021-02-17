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

"""
Test the file recognizer capabilities.
"""

import errno
import gzip
import os
import shutil
import socket
import sys
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from grin import GZIP_MAGIC, FileRecognizer


@contextmanager
def cd(newdir):
    prevdir = os.getcwd()
    os.chdir(os.path.expanduser(newdir))
    try:
        yield
    finally:
        os.chdir(prevdir)


class FilesTextCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.oldcwd = Path.cwd()
        cls.tempdir = TemporaryDirectory()
        os.chdir(cls.tempdir.name)
        cls.setup()

    @classmethod
    def tearDownClass(cls):
        cls.cleanup()
        _socket_file = getattr(cls, "_socket_file", None)
        if _socket_file:
            _socket_file.close()
        os.chdir(str(cls.oldcwd))
        cls.tempdir.cleanup()

    @classmethod
    def empty_file(cls, filename, open=open):
        with open(filename, "wb"):
            pass

    @classmethod
    def binary_file(cls, filename, open=open):
        with open(filename, "wb") as f:
            f.write(bytes(range(255)))

    @classmethod
    def text_file(cls, filename, open=open):
        lines = [b"foo\n", b"bar\n"] * 100
        lines.append(b"baz\n")
        lines.extend([b"foo\n", b"bar\n"] * 100)
        with open(filename, "wb") as f:
            f.writelines(lines)

    @classmethod
    def fake_gzip_file(cls, filename, open=open):
        """Write out a binary file that has the gzip magic header bytes, but is not
        a gzip file.
        """
        with open(filename, "wb") as f:
            f.write(GZIP_MAGIC)
            f.write(bytes(range(255)))

    @classmethod
    def binary_middle(cls, filename, open=open):
        """Write out a file that is text for the first 100 bytes, then 100 binary
        bytes, then 100 text bytes to test that the recognizer only reads some of
        the file.
        """
        text = b"a" * 100 + b"\0" * 100 + b"b" * 100
        with open(filename, "wb") as f:
            f.write(text)

    @classmethod
    def socket_file(cls, filename):
        cls._socket_file = socket.socket(socket.AF_UNIX)
        cls._socket_file.bind(filename)

    @classmethod
    def unreadable_file(cls, filename):
        """Write a file that does not have read permissions."""
        cls.text_file(filename)
        os.chmod(filename, 0o200)

    @classmethod
    def unreadable_dir(cls, filename):
        """Make a directory that does not have read permissions."""
        os.mkdir(filename)
        os.chmod(filename, 0o300)

    @classmethod
    def unexecutable_dir(cls, filename):
        """Make a directory that does not have execute permissions."""
        os.mkdir(filename)
        os.chmod(filename, 0o600)

    @classmethod
    def totally_unusable_dir(cls, filename):
        """Make a directory that has neither read nor execute permissions."""
        os.mkdir(filename)
        os.chmod(filename, 0o100)

    @classmethod
    def setup(cls):
        # Make files to test individual recognizers.
        cls.empty_file("empty")
        cls.binary_file("binary")
        cls.binary_middle("binary_middle")
        cls.text_file("text")
        cls.text_file("text~")
        cls.text_file("text#")
        cls.text_file("foo.bar.baz")
        os.mkdir("dir")
        cls.binary_file(".binary")
        cls.text_file(".text")
        cls.empty_file("empty.gz", open=gzip.open)
        cls.binary_file("binary.gz", open=gzip.open)
        cls.text_file("text.gz", open=gzip.open)
        cls.binary_file(".binary.gz", open=gzip.open)
        cls.text_file(".text.gz", open=gzip.open)
        cls.fake_gzip_file("fake.gz")
        os.mkdir(".dir")
        os.symlink("binary", "binary_link")
        os.symlink("text", "text_link")
        os.symlink("dir", "dir_link")
        os.symlink(".binary", ".binary_link")
        os.symlink(".text", ".text_link")
        os.symlink(".dir", ".dir_link")
        cls.unreadable_file("unreadable_file")
        cls.unreadable_dir("unreadable_dir")
        cls.unexecutable_dir("unexecutable_dir")
        cls.totally_unusable_dir("totally_unusable_dir")
        os.symlink("unreadable_file", "unreadable_file_link")
        os.symlink("unreadable_dir", "unreadable_dir_link")
        os.symlink("unexecutable_dir", "unexecutable_dir_link")
        os.symlink("totally_unusable_dir", "totally_unusable_dir_link")
        cls.text_file("text.skip_ext")
        os.mkdir("dir.skip_ext")
        cls.text_file("text.dont_skip_ext")
        os.mkdir("skip_dir")
        cls.text_file("fake_skip_dir")
        cls.socket_file("socket_test")

        # Make a directory tree to test tree-walking.
        os.mkdir("tree")
        os.mkdir("tree/.hidden_dir")
        os.mkdir("tree/dir")
        os.mkdir("tree/dir/subdir")
        cls.text_file("tree/dir/text")
        cls.text_file("tree/dir/subdir/text")
        cls.text_file("tree/text")
        cls.text_file("tree/text.skip_ext")
        os.mkdir("tree/dir.skip_ext")
        cls.text_file("tree/dir.skip_ext/text")
        cls.text_file("tree/text.dont_skip_ext")
        cls.binary_file("tree/binary")
        os.mkdir("tree/skip_dir")
        cls.text_file("tree/skip_dir/text")
        os.mkdir("tree/.skip_hidden_dir")
        cls.text_file("tree/.skip_hidden_file")
        os.mkdir("tree/unreadable_dir")
        cls.text_file("tree/unreadable_dir/text")
        os.chmod("tree/unreadable_dir", 0o300)
        os.mkdir("tree/unexecutable_dir")
        cls.text_file("tree/unexecutable_dir/text")
        os.chmod("tree/unexecutable_dir", 0o600)
        os.mkdir("tree/totally_unusable_dir")
        cls.text_file("tree/totally_unusable_dir/text")
        os.chmod("tree/totally_unusable_dir", 0o100)

    @classmethod
    def cleanup(cls):
        files_to_delete = [
            "empty",
            "binary",
            "binary_middle",
            "text",
            "text~",
            "empty.gz",
            "binary.gz",
            "text.gz",
            "dir",
            "binary_link",
            "text_link",
            "dir_link",
            ".binary",
            ".text",
            ".binary.gz",
            ".text.gz",
            "fake.gz",
            ".dir",
            ".binary_link",
            ".text_link",
            ".dir_link",
            "unreadable_file",
            "unreadable_dir",
            "unexecutable_dir",
            "totally_unusable_dir",
            "unreadable_file_link",
            "unreadable_dir_link",
            "unexecutable_dir_link",
            "totally_unusable_dir_link",
            "text.skip_ext",
            "text.dont_skip_ext",
            "dir.skip_ext",
            "skip_dir",
            "fake_skip_dir",
            "text#",
            "foo.bar.baz",
        ]
        for filename in files_to_delete:
            try:
                if os.path.islink(filename) or os.path.isfile(filename):
                    os.unlink(filename)
                else:
                    os.rmdir(filename)
            except Exception as e:
                print("Could not delete %s: %s" % (filename, e), file=sys.stderr)
        os.unlink("socket_test")
        for dirpath, dirnames, filenames in os.walk("tree"):
            # Make sure every directory can be deleted
            for dirname in dirnames:
                os.chmod(os.path.join(dirpath, dirname), 0o700)
        shutil.rmtree("tree")

    # This class tests what the recognizer does if no DirEntry is provided.
    # These are overridden in FilesTextCase_DirEntry to provide DirEntry's.
    def _recognize(self, filename, fr):
        return fr.recognize(filename, None)

    def _recognize_file(self, filename, fr):
        return fr.recognize(filename, None)

    def _recognize_directory(self, dirname, fr):
        return fr.recognize_directory(dirname, None)

    def test_binary(self):
        fr = FileRecognizer()
        self.assertTrue(fr.is_binary("binary"))
        self.assertEqual(self._recognize_file("binary", fr), "binary")
        self.assertEqual(self._recognize("binary", fr), "binary")

    def test_text(self):
        fr = FileRecognizer()
        self.assertFalse(fr.is_binary("text"))
        self.assertEqual(self._recognize_file("text", fr), "text")
        self.assertEqual(self._recognize("text", fr), "text")

    def test_gzipped(self):
        fr = FileRecognizer()
        self.assertTrue(fr.is_binary("text.gz"))
        self.assertEqual(self._recognize_file("text.gz", fr), "gzip")
        self.assertEqual(self._recognize("text.gz", fr), "gzip")
        self.assertTrue(fr.is_binary("binary.gz"))
        self.assertEqual(self._recognize_file("binary.gz", fr), "binary")
        self.assertEqual(self._recognize("binary.gz", fr), "binary")
        self.assertTrue(fr.is_binary("fake.gz"))
        self.assertEqual(self._recognize_file("fake.gz", fr), "binary")
        self.assertEqual(self._recognize("fake.gz", fr), "binary")

    def test_binary_middle(self):
        fr = FileRecognizer(binary_bytes=100)
        self.assertFalse(fr.is_binary("binary_middle"))
        self.assertEqual(self._recognize_file("binary_middle", fr), "text")
        self.assertEqual(self._recognize("binary_middle", fr), "text")
        fr = FileRecognizer(binary_bytes=101)
        self.assertTrue(fr.is_binary("binary_middle"))
        self.assertEqual(self._recognize_file("binary_middle", fr), "binary")
        self.assertEqual(self._recognize("binary_middle", fr), "binary")

    def test_socket(self):
        fr = FileRecognizer()
        self.assertEqual(self._recognize("socket_test", fr), "skip")

    def test_dir(self):
        fr = FileRecognizer()
        self.assertEqual(self._recognize_directory("dir", fr), "directory")
        self.assertEqual(self._recognize("dir", fr), "directory")

    def test_skip_symlinks(self):
        fr = FileRecognizer(skip_symlink_files=True, skip_symlink_dirs=True)
        self.assertEqual(self._recognize("binary_link", fr), "link")
        self.assertEqual(self._recognize_file("binary_link", fr), "link")
        self.assertEqual(self._recognize("text_link", fr), "link")
        self.assertEqual(self._recognize_file("text_link", fr), "link")
        self.assertEqual(self._recognize("dir_link", fr), "link")
        self.assertEqual(self._recognize_directory("dir_link", fr), "link")

    def test_do_not_skip_symlinks(self):
        fr = FileRecognizer(skip_symlink_files=False, skip_symlink_dirs=False)
        self.assertEqual(self._recognize("binary_link", fr), "binary")
        self.assertEqual(self._recognize_file("binary_link", fr), "binary")
        self.assertEqual(self._recognize("text_link", fr), "text")
        self.assertEqual(self._recognize_file("text_link", fr), "text")
        self.assertEqual(self._recognize("dir_link", fr), "directory")
        self.assertEqual(self._recognize_directory("dir_link", fr), "directory")

    def test_skip_hidden(self):
        fr = FileRecognizer(skip_hidden_files=True, skip_hidden_dirs=True)
        self.assertEqual(self._recognize(".binary", fr), "skip")
        self.assertEqual(self._recognize_file(".binary", fr), "skip")
        self.assertEqual(self._recognize(".text", fr), "skip")
        self.assertEqual(self._recognize_file(".text", fr), "skip")
        self.assertEqual(self._recognize(".dir", fr), "skip")
        self.assertEqual(self._recognize_directory(".dir", fr), "skip")
        self.assertEqual(self._recognize(".binary_link", fr), "skip")
        self.assertEqual(self._recognize_file(".binary_link", fr), "skip")
        self.assertEqual(self._recognize(".text_link", fr), "skip")
        self.assertEqual(self._recognize_file(".text_link", fr), "skip")
        self.assertEqual(self._recognize(".dir_link", fr), "skip")
        self.assertEqual(self._recognize_directory(".dir_link", fr), "skip")
        self.assertEqual(self._recognize(".text.gz", fr), "skip")
        self.assertEqual(self._recognize_file(".text.gz", fr), "skip")
        self.assertEqual(self._recognize(".binary.gz", fr), "skip")
        self.assertEqual(self._recognize_file(".binary.gz", fr), "skip")

    def test_skip_backup(self):
        fr = FileRecognizer(skip_backup_files=True)
        self.assertEqual(self._recognize_file("text~", fr), "skip")

    def test_do_not_skip_backup(self):
        fr = FileRecognizer(skip_backup_files=False)
        self.assertEqual(self._recognize_file("text~", fr), "text")

    def test_skip_weird_exts(self):
        fr = FileRecognizer(skip_exts=set())
        self.assertEqual(self._recognize_file("text#", fr), "text")
        self.assertEqual(self._recognize_file("foo.bar.baz", fr), "text")
        fr = FileRecognizer(skip_exts=set(["#", ".bar.baz"]))
        self.assertEqual(self._recognize_file("text#", fr), "skip")
        self.assertEqual(self._recognize_file("foo.bar.baz", fr), "skip")

    def test_do_not_skip_hidden_or_symlinks(self):
        fr = FileRecognizer(
            skip_hidden_files=False,
            skip_hidden_dirs=False,
            skip_symlink_dirs=False,
            skip_symlink_files=False,
        )
        self.assertEqual(self._recognize(".binary", fr), "binary")
        self.assertEqual(self._recognize_file(".binary", fr), "binary")
        self.assertEqual(self._recognize(".text", fr), "text")
        self.assertEqual(self._recognize_file(".text", fr), "text")
        self.assertEqual(self._recognize(".dir", fr), "directory")
        self.assertEqual(self._recognize_directory(".dir", fr), "directory")
        self.assertEqual(self._recognize(".binary_link", fr), "binary")
        self.assertEqual(self._recognize_file(".binary_link", fr), "binary")
        self.assertEqual(self._recognize(".text_link", fr), "text")
        self.assertEqual(self._recognize_file(".text_link", fr), "text")
        self.assertEqual(self._recognize(".dir_link", fr), "directory")
        self.assertEqual(self._recognize_directory(".dir_link", fr), "directory")
        self.assertEqual(self._recognize(".text.gz", fr), "gzip")
        self.assertEqual(self._recognize_file(".text.gz", fr), "gzip")
        self.assertEqual(self._recognize(".binary.gz", fr), "binary")
        self.assertEqual(self._recognize_file(".binary.gz", fr), "binary")

    def test_do_not_skip_hidden_but_skip_symlinks(self):
        fr = FileRecognizer(
            skip_hidden_files=False,
            skip_hidden_dirs=False,
            skip_symlink_dirs=True,
            skip_symlink_files=True,
        )
        self.assertEqual(self._recognize(".binary", fr), "binary")
        self.assertEqual(self._recognize_file(".binary", fr), "binary")
        self.assertEqual(self._recognize(".text", fr), "text")
        self.assertEqual(self._recognize_file(".text", fr), "text")
        self.assertEqual(self._recognize(".dir", fr), "directory")
        self.assertEqual(self._recognize_directory(".dir", fr), "directory")
        self.assertEqual(self._recognize(".binary_link", fr), "link")
        self.assertEqual(self._recognize_file(".binary_link", fr), "link")
        self.assertEqual(self._recognize(".text_link", fr), "link")
        self.assertEqual(self._recognize_file(".text_link", fr), "link")
        self.assertEqual(self._recognize(".dir_link", fr), "link")
        self.assertEqual(self._recognize_directory(".dir_link", fr), "link")
        self.assertEqual(self._recognize(".text.gz", fr), "gzip")
        self.assertEqual(self._recognize_file(".text.gz", fr), "gzip")
        self.assertEqual(self._recognize(".binary.gz", fr), "binary")
        self.assertEqual(self._recognize_file(".binary.gz", fr), "binary")

    def test_lack_of_permissions(self):
        fr = FileRecognizer()
        self.assertEqual(self._recognize("unreadable_file", fr), "unreadable")
        self.assertEqual(self._recognize_file("unreadable_file", fr), "unreadable")
        self.assertEqual(self._recognize("unreadable_dir", fr), "directory")
        self.assertEqual(self._recognize_directory("unreadable_dir", fr), "directory")
        self.assertEqual(self._recognize("unexecutable_dir", fr), "directory")
        self.assertEqual(self._recognize_directory("unexecutable_dir", fr), "directory")
        self.assertEqual(self._recognize("totally_unusable_dir", fr), "directory")
        self.assertEqual(self._recognize_directory("totally_unusable_dir", fr), "directory")

    def test_symlink_src_unreadable(self):
        fr = FileRecognizer(skip_symlink_files=False, skip_symlink_dirs=False)
        self.assertEqual(self._recognize("unreadable_file_link", fr), "unreadable")
        self.assertEqual(self._recognize_file("unreadable_file_link", fr), "unreadable")
        self.assertEqual(self._recognize("unreadable_dir_link", fr), "directory")
        self.assertEqual(self._recognize_directory("unreadable_dir_link", fr), "directory")
        self.assertEqual(self._recognize("unexecutable_dir_link", fr), "directory")
        self.assertEqual(self._recognize_directory("unexecutable_dir_link", fr), "directory")
        self.assertEqual(self._recognize("totally_unusable_dir_link", fr), "directory")
        self.assertEqual(self._recognize_directory("totally_unusable_dir_link", fr), "directory")

    def test_skip_ext(self):
        fr = FileRecognizer(skip_exts=set([".skip_ext", "~"]))
        self.assertEqual(self._recognize("text.skip_ext", fr), "skip")
        self.assertEqual(self._recognize_file("text.skip_ext", fr), "skip")
        self.assertEqual(self._recognize("text", fr), "text")
        self.assertEqual(self._recognize_file("text", fr), "text")
        self.assertEqual(self._recognize("text.dont_skip_ext", fr), "text")
        self.assertEqual(self._recognize_file("text.dont_skip_ext", fr), "text")
        self.assertEqual(self._recognize("dir.skip_ext", fr), "directory")
        self.assertEqual(self._recognize_directory("dir.skip_ext", fr), "directory")
        self.assertEqual(self._recognize_file("text~", fr), "skip")

    def test_skip_dir(self):
        fr = FileRecognizer(skip_dirs=set(["skip_dir", "fake_skip_dir"]))
        self.assertEqual(self._recognize("skip_dir", fr), "skip")
        self.assertEqual(self._recognize_directory("skip_dir", fr), "skip")
        self.assertEqual(self._recognize("fake_skip_dir", fr), "text")
        self.assertEqual(self._recognize_file("fake_skip_dir", fr), "text")

    def test_walking(self):
        fr = FileRecognizer(
            skip_hidden_files=True,
            skip_hidden_dirs=True,
            skip_exts=set([".skip_ext"]),
            skip_dirs=set(["skip_dir"]),
        )
        truth = [
            ("tree/binary", "binary"),
            ("tree/dir.skip_ext/text", "text"),
            ("tree/dir/subdir/text", "text"),
            ("tree/dir/text", "text"),
            ("tree/text", "text"),
            ("tree/text.dont_skip_ext", "text"),
        ]
        result = sorted(fr.walk("tree"))
        self.assertEqual(result, truth)

    def test_dot(self):
        with cd("tree"):
            fr = FileRecognizer(
                skip_hidden_files=True,
                skip_hidden_dirs=True,
                skip_exts=set([".skip_ext"]),
                skip_dirs=set(["skip_dir"]),
            )
            truth = [
                ("./binary", "binary"),
                ("./dir.skip_ext/text", "text"),
                ("./dir/subdir/text", "text"),
                ("./dir/text", "text"),
                ("./text", "text"),
                ("./text.dont_skip_ext", "text"),
            ]
            result = sorted(fr.walk("."))
            self.assertEqual(result, truth)

    def test_dot_dot(self):
        with cd("tree/dir"):
            fr = FileRecognizer(
                skip_hidden_files=True,
                skip_hidden_dirs=True,
                skip_exts=set([".skip_ext"]),
                skip_dirs=set(["skip_dir"]),
            )
            truth = [
                ("../binary", "binary"),
                ("../dir.skip_ext/text", "text"),
                ("../dir/subdir/text", "text"),
                ("../dir/text", "text"),
                ("../text", "text"),
                ("../text.dont_skip_ext", "text"),
            ]
            result = sorted(fr.walk(".."))
            self.assertEqual(result, truth)


class DirEntryFilesTextCase_DirEntry(FilesTextCase):
    """
    Run every test in FilesTextCase, except that the 'direntry' argument is supplied to .recognize,
    .recognize_directory and .recognize_file.
    """

    def _do_recognize(self, filename, fr, method):
        # Working backwards from the filename to the DirEntry record that would have produced it.

        direc, fn = os.path.split(filename)
        direc = "." if direc == "" else direc
        entries = list(os.scandir(direc))
        if entries:
            for dire in entries:
                if dire.name == fn:
                    return method(filename, dire)
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), filename)

    def _recognize(self, filename, fr):
        return self._do_recognize(filename, fr, fr.recognize)

    def _recognize_file(self, filename, fr):
        return self._do_recognize(filename, fr, fr.recognize)

    def _recognize_directory(self, filename, fr):
        return self._do_recognize(filename, fr, fr.recognize_directory)
