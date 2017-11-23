#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2017  Free Software Foundation Europe e.V.
#
# This file is part of reuse, available from its original location:
# <https://git.fsfe.org/reuse/reuse/>.
#
# reuse is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# reuse is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# reuse.  If not, see <http://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0+

"""Misc. utilities for reuse."""

import logging
import shutil
import subprocess
from pathlib import Path
from typing import BinaryIO, List, Optional, Union

import chardet

GIT_EXE = shutil.which('git')

_logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


PathLike = Union[Path, str]  # pylint: disable=invalid-name


def setup_logging(level: int = logging.WARNING) -> None:
    """Configure logging for reuse."""
    # library_logger is the root logger for reuse.  We configure logging solely
    # for reuse, not for any other libraries.
    library_logger = logging.getLogger('reuse')
    library_logger.setLevel(level)

    if not library_logger.hasHandlers():
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        library_logger.addHandler(handler)


def execute_command(
        command: List[str],
        logger: logging.Logger,
        **kwargs) -> subprocess.CompletedProcess:
    """Run the given command with subprocess.run.  Forward kwargs.  Silence
    output into a pipe unless kwargs override it.
    """
    logger.debug('running %s', ' '.join(command))

    stdout = kwargs.get('stdout', subprocess.PIPE)
    stderr = kwargs.get('stderr', subprocess.PIPE)

    return subprocess.run(
        command,
        stdout=stdout,
        stderr=stderr,
        **kwargs)


def find_root() -> Optional[PathLike]:
    """Try to find the root of the project from $PWD.  If none is found, return
    None.
    """
    cwd = Path.cwd()
    if in_git_repo(cwd):
        command = [GIT_EXE, 'rev-parse', '--show-toplevel']
        result = execute_command(command, _logger, cwd=str(cwd))

        if not result.returncode:
            return Path(result.stdout.decode('utf-8')[:-1])
    return None


def in_git_repo(cwd: PathLike = None) -> bool:
    """Is *cwd* inside of a git repository?

    Always return False if git is not installed.
    """
    if GIT_EXE is None:
        return False

    if cwd is None:
        cwd = Path.cwd()

    command = [GIT_EXE, 'status']
    result = execute_command(command, _logger, cwd=str(cwd))

    return not result.returncode


def decoded_text_from_binary(binary_file: BinaryIO, size: int = None) -> str:
    """Given a binary file object, detect its encoding and return its contents
    as a decoded string.  Do not throw any errors if the encoding contains
    errors:  Just replace the false characters.

    If *size* is specified, only read so many bytes.
    """
    rawdata = binary_file.read(size)
    result = chardet.detect(rawdata)
    encoding = result.get('encoding')
    if encoding is None:
        encoding = 'utf-8'
    return rawdata.decode(encoding, errors='replace')
