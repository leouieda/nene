# Copyright (c) 2021 Leonardo Uieda.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT
"""
Core functions used to parse inputs, generate HTML, etc.

Should be independent of the command-line interface so they can be tested in
isolation.
"""
import json
import logging
from pathlib import Path

import livereload
import yaml


def parse_config(fname):
    """
    Load configuration from a JSON file and append to the defaults.

    Parameters
    ----------
    fname : str or :class:`pathlib.Path`
        The name or path of the configuration file (has to be in JSON format).

    Returns
    -------
    config : dict
        A dictionary with the default configuration and variables loaded from
        the file.
    """
    config = {
        "ignore": [],
        "output_dir": "_build",
        "templates_dir": "_templates",
        "copy": [],
    }
    with open(fname) as config_file:
        config.update(json.load(config_file))
    config["ignore"].append(fname)
    return config


def crawl(root, ignore, copy_extra):
    """
    Crawl the directory root separating Markdown, JSON, and files for copying.

    Paths starting with `_` or in *ignore* will not be included.

    Parameters
    ----------
    root : str or :class:`pathlib.Path`
        The base path to start crawling.
    ignore : list of str
        List of paths to ignore when crawling.
    copy_extra : list of str
        List of extra paths to copy to the build directory.

    Returns
    -------
    tree : dict
        A dictionary with keys `"markdown"`, `"json"`, and `"copy"` containing
        lists of Paths that fall in each category. The "copy" list contains
        both files and directories.

    """
    tree = {"copy": [Path(path) for path in copy_extra], "markdown": [], "json": []}
    for path in Path(root).glob("**/*"):
        if str(path) in ignore:
            continue
        if path.parts[0].startswith("_") or path.name.startswith("."):
            continue
        if path.suffix == ".md":
            tree["markdown"].append(path)
        elif path.suffix == ".json":
            tree["json"].append(path)
        else:
            tree["copy"].append(path)
    return tree


def serve_and_watch(path, config_file, watch, extra, quiet):
    """
    Serve the output folder with livereload and watch the tree and extra files.

    Parameters
    ----------
    path : str or :class:`pathlib.Path`
        The path that will be served.
    config_file : str or :class:`pathlib.Path`
        The configuration file used.
    watch : dict
        Dictionary with lists of source files that will be watched for changes.
        Usually the output of :func:`nene.core.crawl`.
    extra : list
        List of extra files to watch.
    quiet: bool
        If True, will set logging output from livereload only at "ERROR" level.

    """
    if quiet:
        logger = logging.getLogger("livereload")
        logger.setLevel("ERROR")
    server = livereload.Server()
    files = list(extra)
    for category in watch:
        files.extend(watch[category])
    for filename in files:
        server.watch(filename, f"nene --config={config_file} --quiet")
    server.serve(root=path, host="localhost", open_url_delay=1)


def load_markdown(path):
    """
    Read Markdown content from path, including YAML front matter.

    Parameters
    ----------
    path : :class:`pathlib.Path`
        The path of the Markdown file.

    Returns
    -------
    page : dict
        Dictionary with the parsed YAML front-matter and Markdown body.
    """
    identifier = str(path.parent / path.stem)
    page = {
        "id": identifier,
        "path": str(path.with_suffix(".html")),
        "source": str(path),
    }
    text = path.read_text()
    front_matter, markdown = text.split("---")[1:]
    page.update(yaml.safe_load(front_matter.strip()))
    page["markdown"] = markdown
    return page
