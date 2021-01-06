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

import argparse
import fnmatch
import os
import shlex
import sys

from .recognizer import get_recognizer

__all__ = ["get_grind_arg_parser"]


def get_grind_arg_parser(parser=None):
    """Create the command-line parser for the find-like companion program."""
    from . import __version__

    if parser is None:
        parser = argparse.ArgumentParser(
            description="Find text and binary files using similar rules as grin.",
            epilog="Bug reports to <enthought-dev@mail.enthought.com>.",
        )

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version="grin %s" % __version__,
        help="show program's version number and exit",
    )
    parser.add_argument(
        "-s",
        "--no-skip-hidden-files",
        dest="skip_hidden_files",
        action="store_false",
        help="do not skip .hidden files",
    )
    parser.add_argument(
        "--skip-hidden-files",
        dest="skip_hidden_files",
        action="store_true",
        default=True,
        help="do skip .hidden files",
    )
    parser.add_argument(
        "-b",
        "--no-skip-backup-files",
        dest="skip_backup_files",
        action="store_false",
        help="do not skip backup~ files [deprecated; edit --skip-exts]",
    )
    parser.add_argument(
        "--skip-backup-files",
        dest="skip_backup_files",
        action="store_true",
        default=True,
        help="do skip backup~ files [default] [deprecated; edit --skip-exts]",
    )
    parser.add_argument(
        "-S",
        "--no-skip-hidden-dirs",
        dest="skip_hidden_dirs",
        action="store_false",
        help="do not skip .hidden directories",
    )
    parser.add_argument(
        "--skip-hidden-dirs",
        dest="skip_hidden_dirs",
        default=True,
        action="store_true",
        help="do skip .hidden directories",
    )
    parser.add_argument(
        "-d",
        "--skip-dirs",
        default="CVS,RCS,.svn,.hg,.bzr,build,dist,target,node_modules",
        help="comma-separated list of directory names to skip [default=%(default)r]",
    )
    parser.add_argument(
        "-D",
        "--no-skip-dirs",
        dest="skip_dirs",
        action="store_const",
        const="",
        help="do not skip any directories",
    )
    parser.add_argument(
        "-e",
        "--skip-exts",
        default=".pyc,.pyo,.so,.o,.a,.tgz,.tar.gz,.rar,.zip,~,#,.bak,.png,.jpg,.gif,.bmp,.tif,.tiff,.pyd,.dll,.exe,.obj,.lib,.class",  # noqa: E501
        help="comma-separated list of file extensions to skip [default=%(default)r]",
    )
    parser.add_argument(
        "-E",
        "--no-skip-exts",
        dest="skip_exts",
        action="store_const",
        const="",
        help="do not skip any file extensions",
    )
    parser.add_argument(
        "--no-follow",
        action="store_false",
        dest="follow_symlinks",
        default=False,
        help="do not follow symlinks to directories and files [default]",
    )
    parser.add_argument(
        "--follow",
        action="store_true",
        dest="follow_symlinks",
        help="follow symlinks to directories and files",
    )
    parser.add_argument(
        "-0",
        "--null-separated",
        action="store_true",
        help="print the filenames separated by NULs",
    )
    parser.add_argument("--dirs", nargs="+", default=["."], help="the directories to start from")
    parser.add_argument("--sys-path", action="store_true", help="search the directories on sys.path")

    parser.add_argument(
        "glob",
        default="*",
        nargs="?",
        help=(  # noqa: E501
            "the glob pattern to match; you may need to quote this to prevent the shell from trying to expand it"
            " [default=%(default)r]"
        ),
    )

    return parser


def print_null(filename):
    # Note that the final filename will have a trailing NUL, just like
    # "find -print0" does.
    sys.stdout.write(filename)
    sys.stdout.write("\0")


def main(argv=None):
    try:
        if argv is None:
            # Look at the GRIND_ARGS environment variable for more arguments.
            env_args = shlex.split(os.getenv("GRIND_ARGS", ""))
            argv = [sys.argv[0]] + env_args + sys.argv[1:]
        parser = get_grind_arg_parser()
        args = parser.parse_args(argv[1:])

        # Define the output function.
        if args.null_separated:
            output = print_null
        else:
            output = print

        if args.sys_path:
            args.dirs.extend(sys.path)

        fr = get_recognizer(args)
        for dir in args.dirs:
            for filename, k in fr.walk(dir):
                if fnmatch.fnmatch(os.path.basename(filename), args.glob):
                    output(filename)
    except KeyboardInterrupt:
        raise SystemExit(0)
    except IOError as e:
        if "Broken pipe" in str(e):
            # The user is probably piping to a pager like less(1) and has exited
            # it. Just exit.
            raise SystemExit(0)
        raise
