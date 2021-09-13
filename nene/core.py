"""
Core functions used to parse inputs and generate HTML
"""
from pathlib import Path
import json
import logging

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
    }
    with open(fname) as config_file:
        config.update(json.load(config_file))
    config["ignore"].append(fname)
    return config


def crawl(root, ignore):
    """
    Crawl the directory root separating Markdown, JSON, and files for copying.

    Paths starting with `_` or in *ignore* will not be included.

    Parameters
    ----------
    root : str or :class:`pathlib.Path`
        The base path to start crawling.
    ignore : list of str
        List of paths to ignore when crawling.

    Returns
    -------
    tree : dict
        A dictionary with keys `"markdown"`, `"json"`, and `"copy"` containing
        lists of Paths that fall in each category. The "copy" list contains
        both files and directories.

    """
    tree = dict(copy=[], markdown=[], json=[])
    for path in Path(root).glob("**/*"):
        if str(path) in ignore or path.parts[0].startswith("_"):
            continue
        if path.suffix == ".md":
            tree["markdown"].append(path)
        elif path.suffix == ".json":
            tree["json"].append(path)
        else:
            tree["copy"].append(path)
    return tree


def serve_and_watch(path, watch, extra, quiet):
    """
    Serve the output folder with livereload and watch the tree and extra files

    Parameters
    ----------
    path : str or :class:`pathlib.Path`
        The path that will be served.
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
        server.watch(filename, "nene build --quiet")
    server.serve(root=path, host="localhost", open_url_delay=1)


def load_markdown(path):
    """
    Read Markdown content from path, including YAML front matter.
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
