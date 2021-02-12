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
import gzip
import os
import re
import shlex
import sys

from .main import GrepText
from .recognizer import get_recognizer
from .utils import get_regex

__all__ = ["get_filenames", "get_grin_arg_parser"]


def get_filenames(args):
    """Generate the filenames to grep.

    Parameters
    ----------
    args : Namespace
        The commandline arguments object.

    Yields
    ------
    filename : str
    kind : either 'text' or 'gzip'
        What kind of file it is.

    Raises
    ------
    IOError if a requested file cannot be found.
    """
    files = []
    # If the user has given us a file with filenames, consume them first.
    if args.files_from_file is not None:
        if args.files_from_file == "-":
            files_file = sys.stdin
            should_close = False
        elif os.path.exists(args.files_from_file):
            files_file = open(args.files_from_file)
            should_close = True
        else:
            raise IOError(2, "No such file: %r" % args.files_from_file)

        try:
            # Remove ''
            # XXX: how can I detect bad filenames? One user accidentally ran
            # grin -f against a binary file and got an unhelpful error message
            # later.
            if args.null_separated:
                files.extend([x.strip() for x in files_file.read().split("\0")])
            else:
                files.extend([x.strip() for x in files_file])
        finally:
            if should_close:
                files_file.close()

    # Now add the filenames provided on the command line itself.
    files.extend(args.files)
    if args.sys_path:
        files.extend(sys.path)
    # Make sure we don't have any empty strings lying around.
    # Also skip certain special null files which may be added by programs like
    # Emacs.
    if sys.platform == "win32":
        upper_bad = set(["NUL:", "NUL"])
        raw_bad = set([""])
    else:
        upper_bad = set()
        raw_bad = set(["", "/dev/null"])
    files = [fn for fn in files if fn not in raw_bad and fn.upper() not in upper_bad]
    if len(files) == 0:
        # Add the current directory at least.
        files = ["."]

    # Go over our list of filenames and see if we can recognize each as
    # something we want to grep.
    fr = get_recognizer(args)
    for fn in files:
        # Special case text stdin.
        if fn == "-":
            yield fn, "text"
            continue
        kind = fr.recognize(fn, None)
        if kind in ("text", "gzip") and fnmatch.fnmatch(os.path.basename(fn), args.include):
            yield fn, kind
        elif kind == "directory":
            for filename, k in fr.walk(fn):
                if k in ("text", "gzip") and fnmatch.fnmatch(os.path.basename(filename), args.include):
                    yield filename, k
        # XXX: warn about other files?
        # XXX: handle binary?


def get_grin_arg_parser(parser=None):
    """Create the command-line parser."""
    from . import __version__

    if parser is None:
        parser = argparse.ArgumentParser(
            description="Search text files for a given regex pattern.",
            epilog="Bug reports to <enthought-dev@mail.enthought.com>.",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version="grin %s" % __version__,
        help="show program's version number and exit",
    )
    parser.add_argument(
        "-i",
        "--ignore-case",
        action="append_const",
        dest="re_flags",
        const=re.I,
        default=[],
        help="ignore case in the regex",
    )
    parser.add_argument(
        "-F",
        "--fixed-string",
        action="store_true",
        dest="fixed_string",
        default=False,
        help="search pattern is fixed string, not regex",
    )
    parser.add_argument(
        "-A",
        "--after-context",
        default=0,
        type=int,
        help="the number of lines of context to show after the match [default=%(default)r]",
    )
    parser.add_argument(
        "-B",
        "--before-context",
        default=0,
        type=int,
        help="the number of lines of context to show before the match [default=%(default)r]",
    )
    parser.add_argument(
        "-C",
        "--context",
        type=int,
        help="the number of lines of context to show on either side of the match",
    )
    parser.add_argument(
        "-I",
        "--include",
        default="*",
        help="only search in files matching this glob [default=%(default)r]",
    )
    parser.add_argument(
        "-n",
        "--line-number",
        action="store_true",
        dest="show_line_numbers",
        default=True,
        help="show the line numbers [default]",
    )
    parser.add_argument(
        "-N",
        "--no-line-number",
        action="store_false",
        dest="show_line_numbers",
        help="do not show the line numbers",
    )
    parser.add_argument(
        "-H",
        "--with-filename",
        action="store_true",
        dest="show_filename",
        default=True,
        help="show the filenames of files that match [default]",
    )
    parser.add_argument(
        "--without-filename",
        action="store_false",
        dest="show_filename",
        help="do not show the filenames of files that match",
    )
    parser.add_argument(
        "--emacs",
        action="store_true",
        dest="show_emacs",
        help="print the filename with every match for easier parsing by e.g. Emacs",
    )
    parser.add_argument(
        "-l",
        "--files-with-matches",
        action="store_false",
        dest="show_match",
        help="show only the filenames and not the texts of the matches",
    )
    parser.add_argument(
        "-L",
        "--files-without-matches",
        action="store_true",
        dest="show_match",
        default=False,
        help="show the matches with the filenames",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        default=sys.platform == "win32",
        help="do not use colorized output [default if piping the output]",
    )
    parser.add_argument(
        "--use-color",
        action="store_false",
        dest="no_color",
        help="use colorized output [default if outputting to a terminal]",
    )
    parser.add_argument(
        "--force-color",
        action="store_true",
        help="always use colorized output even when piping to something that may not be able to handle it",
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
        help="do skip .hidden files [default]",
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
        help="do skip .hidden directories [default]",
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
        "-f",
        "--files-from-file",
        metavar="FILE",
        help="read files to search from a file, one per line; - for stdin",
    )
    parser.add_argument(
        "-0",
        "--null-separated",
        action="store_true",
        help="filenames specified in --files-from-file are separated by NULs",
    )
    parser.add_argument("--sys-path", action="store_true", help="search the directories on sys.path")

    parser.add_argument(
        "-x",
        "--encoding",
        default=sys.stdout.encoding,
        help="Encoding from which to open the included files from in order for the regex"
        " and the stdout output to work properly. Default to your terminal output encoding.",
    )
    parser.add_argument("regex", help="the regular expression to search for")
    parser.add_argument("files", nargs="*", help="the files to search")

    return parser


def main(argv=None):
    try:
        if argv is None:
            # Look at the GRIN_ARGS environment variable for more arguments.
            env_args = shlex.split(os.getenv("GRIN_ARGS", ""))
            argv = [sys.argv[0]] + env_args + sys.argv[1:]
        parser = get_grin_arg_parser()
        args = parser.parse_args(argv[1:])
        if args.context is not None:
            args.before_context = args.context
            args.after_context = args.context

        use_term_color = not args.no_color and sys.stdout.isatty() and (os.environ.get("TERM") != "dumb")
        args.use_color = args.force_color or use_term_color

        regex = get_regex(args)
        g = GrepText(regex, args)
        openers = dict(text=open, gzip=gzip.open)
        for filename, kind in get_filenames(args):
            report = g.grep_a_file(filename, opener=openers[kind], encoding=args.encoding)
            sys.stdout.write(report)
    except KeyboardInterrupt:
        raise SystemExit(0)
    except IOError as e:
        if "Broken pipe" in str(e):
            # The user is probably piping to a pager like less(1) and has exited
            # it. Just exit.
            raise SystemExit(0)
        raise
