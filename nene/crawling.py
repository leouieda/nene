# Copyright (c) 2021 Leonardo Uieda.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT
"""Find files by crawling a directory tree."""
from glob import glob
from pathlib import Path


def _walk_non_hidden(root, hidden_start=(".", "_")):
    """
    Walk a directory tree while ignoring paths that start with some markers.

    Parameters
    ----------
    root : str or :class:`pathlib.Path`
        The base path to start crawling.
    hidden_start : tuple of str
        List of starting characters to ignore.

    Yields
    ------
    path : str or :class:`pathlib.Path`
        Path to a file.
    """
    for path in Path(root).glob("*"):
        if not any(path.name.startswith(hidden) for hidden in hidden_start):
            if path.is_dir():
                yield from _walk_non_hidden(path, hidden_start)
            else:
                yield path


def crawl(root, ignore, copy_extra):
    """
    Crawl the directory root separating inputs by type and files for copying.

    Paths starting with `_` and `.` or in *ignore* will not be included.

    Parameters
    ----------
    root : str or :class:`pathlib.Path`
        The base path to start crawling.
    ignore : list of str
        List of paths to ignore when crawling. Paths can contain globbing syntax.
    copy_extra : list of str
        List of extra paths to copy to the build directory.

    Returns
    -------
    tree : dict
        A dictionary with keys `"markdown"`, `"ipynb"`, `"json"`, and `"copy"`
        containing lists of Paths that fall in each category.

    """
    formats = {
        ".md": "markdown",
        ".json": "json",
        ".yml": "yaml",
        ".yaml": "yaml",
        ".ipynb": "ipynb",
        ".bib": "bibtex",
    }
    tree = {
        "copy": [Path(path) for path in copy_extra],
        "markdown": [],
        "ipynb": [],
        "json": [],
        "yaml": [],
        "bibtex": [],
    }
    expanded_ignore = []
    for path in ignore:
        expanded_ignore.extend(glob(path, recursive=True))
    for path in _walk_non_hidden(root):
        if str(path) in expanded_ignore:
            continue
        if path.suffix in formats:
            tree[formats[path.suffix]].append(path)
        else:
            tree["copy"].append(path)
    return tree
