# Copyright (c) 2021 Leonardo Uieda.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT
"""
Core functions used to parse inputs, generate HTML, etc.

Should be independent of the command-line interface so they can be tested in
isolation.
"""
import contextlib
import datetime
import json
import logging
import os.path
import subprocess
from pathlib import Path

import livereload
import myst_parser.main
import yaml

try:
    import nbconvert
    import nbformat
    import traitlets.config
except ImportError:
    traitlets = None
    nbconvert = None
    nbformat = None


from . import __version__ as nene_version


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


def parse_data_file(path):
    """
    Read the contents of a data file in JSON or YAML format.

    Parameters
    ----------
    path : :class:`pathlib.Path`
        The path of the JSON or YAML data file.

    Returns
    -------
    data : dict
        The contents of the file as a dictionary.
    """
    path = Path(path)
    suffix = path.suffix
    loader = {".yml": yaml.safe_load, ".yaml": yaml.safe_load, ".json": json.loads}
    data = loader[suffix](path.read_text(encoding="utf-8"))
    return data


def parse_config(fname):
    """
    Load configuration from a JSON or YAML file and append to the defaults.

    Parameters
    ----------
    fname : str or :class:`pathlib.Path`
        The name or path of the configuration file (has to be in JSON or YAML
        format).

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
    config.update(parse_data_file(fname))
    config["ignore"].append(fname)
    return config


def walk_non_hidden(root, hidden_start=(".", "_")):
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
                yield from walk_non_hidden(path, hidden_start)
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
        List of paths to ignore when crawling.
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
    }
    tree = {
        "copy": [Path(path) for path in copy_extra],
        "markdown": [],
        "ipynb": [],
        "json": [],
        "yaml": [],
    }
    for path in walk_non_hidden(root):
        if str(path) in ignore:
            continue
        if path.suffix in formats:
            tree[formats[path.suffix]].append(path)
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
    identifier = generate_identifier(path)
    page = {
        "id": identifier,
        "type": "markdown",
        "parent": str(path.parent),
        "path": str(path.with_suffix(".html")),
        "source": str(path),
    }
    text = path.read_text(encoding="utf-8")
    front_matter, markdown = text.split("---")[1:]
    page.update(yaml.safe_load(front_matter.strip()))
    page["markdown"] = markdown
    return page


def load_jupyter_notebook(path):
    """
    Read Jupyter notebook content as Markdown.

    Parameters
    ----------
    path : :class:`pathlib.Path`
        The path of the notebook file.

    Returns
    -------
    page : dict
        Dictionary with notebook content converted to HTML.
    """
    if nbconvert is None or nbformat is None:
        raise ValueError("Need nbconvert and nbformat to read Jupyter notebook files.")
    identifier = generate_identifier(path)
    page = {
        "id": identifier,
        "type": "ipynb",
        "parent": str(path.parent),
        "path": str(path.with_suffix(".html")),
        "source": str(path),
    }
    notebook = nbformat.reads(path.read_text(encoding="utf-8"), as_version=4)
    image_dir = str(path.stem) + "_images"
    nbconfig = traitlets.config.Config()
    nbconfig.ExtractOutputPreprocessor.output_filename_template = os.path.join(
        image_dir, "{unique_key}_{cell_index}_{index}{extension}"
    )
    exporter = nbconvert.MarkdownExporter(config=nbconfig)
    markdown, resources = exporter.from_notebook_node(notebook)
    page["markdown"] = markdown
    page["images"] = resources["outputs"]
    return page


def load_data(path):
    """
    Read JSON and YAML data from path.

    Parameters
    ----------
    path : :class:`pathlib.Path`
        The path of the JSON or YAML data file.

    Returns
    -------
    data : dict
        Dictionary with the file ID in ``"id"`` and the data in ``"content"``.
    """
    identifier = generate_identifier(path)
    data = {
        "id": identifier,
        "type": "json",
        "parent": str(path.parent),
        "source": str(path),
    }
    data["content"] = parse_data_file(path)
    return data


def markdown_to_html(page, jinja_env, config, site, build):
    """
    Convert Markdown to HTML.

    Renders templating constructs in Markdown sources (only if the source file
    is .md).

    Parameters
    ----------
    page : dict
        Dictionary with the parsed YAML front-matter and Markdown body.
    jinja_env
        A Jinja2 environment for loading templates.
    config : dict
        A dictionary with the default configuration and variables loaded from
        the file.
    site : dict
        Dictionary with the entire site content so far.
    build : dict
        Dictionary with information about the build environment.

    Returns
    -------
    html : str
        The converted HTML.

    """
    if page["source"].endswith(".md"):
        # Jinja doesn't allow \ as paths even on Windows
        # https://github.com/pallets/jinja/issues/711
        template = jinja_env.get_template(str(page["source"]).replace("\\", "/"))
        markdown = template.render(page=page, config=config, site=site, build=build)
    else:
        markdown = page["markdown"]
    return myst_parser.main.to_html(markdown)
