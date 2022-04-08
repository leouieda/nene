# Copyright (c) 2021 Leonardo Uieda.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT
"""Utilities for printing things with the Rich Console."""

import rich.console


def make_console(verbose, style="bold blue"):
    """
    Start up the :class:`rich.console.Console` instance we'll use.

    Parameters
    ----------
    verbose : bool
        Whether or not to print status messages to stderr.
    """
    console = rich.console.Console(stderr=True, quiet=not verbose, highlight=False)
    return console, style


def print_dict(dictionary, console):
    """
    Print the key/value pairs of a dictionary one per line.

    Parameters
    ----------
    dictionary : dict
        The dict.
    console : rich.console.Console
        The console used for printing.
    """
    for key in sorted(dictionary):
        value = dictionary[key]
        if isinstance(value, str):
            value = " ".join([part.strip() for part in value.split("\n")])
        console.print(f"   {key}: {value}", highlight=False)


def print_file_stats(files, console):
    """
    Print the number of files of each type.

    Parameters
    ----------
    files : dict
        Dictionary with lists of files separated by file type.
    console : rich.console.Console
        The console used for printing.
    """
    line_length = max(len(key) for key in files)
    for file_type in files:
        file_type_print = " " * (line_length - len(file_type)) + file_type
        console.print(f"   {file_type_print} = {len(files[file_type])}")
