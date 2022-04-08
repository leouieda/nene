# Copyright (c) 2021 Leonardo Uieda.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT
"""Misc utilities."""
import contextlib
import datetime
import subprocess

from ._version import __version__ as nene_version


def generate_identifier(path):
    """
    Generate a unique identifier for the given path.

    Parameters
    ----------
    path : :class:`pathlib.Path`
        The path of the source file.

    Returns
    -------
    identifier : str
        String of ``/`` separated parents and stem of the path.

    """
    identifier = "/".join([str(i) for i in path.parts[:-1]] + [path.stem])
    return identifier


def capture_build_info():
    """
    Create a dictionary with information about the build environment.

    Returns
    -------
    build : dict
        Dictionary with the captured information.
    """
    build = {
        "today": datetime.datetime.utcnow(),
        "nene_version": nene_version,
    }
    # Have to be careful if git isn't installed or if not running in a repository
    with contextlib.suppress(Exception):
        git_output = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True
        )
        commit = git_output.stdout.strip()
        if commit:
            build["commit"] = commit
    return build
