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
import os.path
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
    tree = {
        "copy": [Path(path) for path in copy_extra],
        "markdown": [],
        "ipynb": [],
        "json": [],
    }
    for path in walk_non_hidden(root):
        if str(path) in ignore:
            continue
        if path.suffix == ".md":
            tree["markdown"].append(path)
        elif path.suffix == ".json":
            tree["json"].append(path)
        elif path.suffix == ".ipynb":
            tree["ipynb"].append(path)
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
    identifier = "/".join([str(i) for i in path.parents] + [path.stem])
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
    text = path.read_text()
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
    notebook = nbformat.reads(path.read_text(), as_version=4)
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


def load_json(path):
    """
    Read JSON  data from path.

    Parameters
    ----------
    path : :class:`pathlib.Path`
        The path of the JSON file.

    Returns
    -------
    data : dict
        Dictionary with the file ID in ``"id"`` and the JSON data in
        ``"json"``.
    """
    identifier = generate_identifier(path)
    data = {
        "id": identifier,
        "type": "json",
        "parent": str(path.parent),
        "source": str(path),
        "json": json.loads(path.read_text()),
    }
    return data


def markdown_to_html(page, jinja_env, config, site):
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

    Returns
    -------
    html : str
        The converted HTML.

    """
    if page["source"].endswith(".md"):
        template = jinja_env.get_template(page["source"])
        markdown = template.render(page=page, config=config, site=site)
    else:
        markdown = page["markdown"]
    return myst_parser.main.to_html(markdown)
