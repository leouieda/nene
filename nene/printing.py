# Copyright (c) 2021 Leonardo Uieda.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT
"""Utilities for printing things with the Rich Console."""

import rich.console


def make_console(verbose):
    """
    Start up the :class:`rich.console.Console` instance we'll use.

    Parameters
    ----------
    verbose : bool
        Whether or not to print status messages to stderr.
    """
    return rich.console.Console(stderr=True, quiet=not verbose, highlight=False)


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
