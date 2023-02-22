# Copyright (c) 2021 Leonardo Uieda.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT
"""Load data from source files."""
import json
from pathlib import Path

import yaml

# For Jupyter notebook support
try:
    import nbconvert
    import nbformat
    import traitlets.config
except ImportError:
    traitlets = None
    nbconvert = None
    nbformat = None

# For bibtex support
try:
    import bibtexparser
    from bibtexparser.bparser import BibTexParser
    from bibtexparser.customization import convert_to_unicode

except ImportError:
    bibtexparser = None

from .utils import generate_identifier


def _read_data_file(path):
    """
    Read the contents of a data file in JSON, YAML or BibTeX format.

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


def _read_bibtex_file(path):
    """
    Read bibtex entries from path.

    Parameters
    ----------
    path : :class:`pathlib.Path`
        The path of the bibtex file.

    Returns
    -------
    data : dict
        The publication entries of the bibfile as a dictionary.
    """
    parser = BibTexParser()
    parser.customization = convert_to_unicode
    with open(path) as bibtex_file:
        bibtex_database = bibtexparser.load(bibtex_file, parser=parser)
    return bibtex_database.entries


def load_config(fname):
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
        "config_file": str(fname),
    }
    config.update(_read_data_file(fname))
    config["ignore"].append(fname)
    return config


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
    if bibtexparser is not None and path.suffix == ".bib":
        content = _read_bibtex_file(path)
    else:
        content = _read_data_file(path)
    data = {
        "id": identifier,
        "type": "data",
        "parent": str(path.parent),
        "source": str(path),
        "content": content,
    }
    return data


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
        "source": str(path),
    }
    text = path.read_text(encoding="utf-8").strip()
    _, front_matter, markdown = text.split("---", maxsplit=2)
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
        "source": str(path),
    }
    notebook = nbformat.reads(path.read_text(encoding="utf-8"), as_version=4)
    image_dir = str(path.stem) + "_images"
    nbconfig = traitlets.config.Config()
    nbconfig.ExtractOutputPreprocessor.output_filename_template = str(
        Path(image_dir) / "{unique_key}_{cell_index}_{index}{extension}"
    )
    exporter = nbconvert.MarkdownExporter(config=nbconfig)
    markdown, resources = exporter.from_notebook_node(notebook)
    page["markdown"] = markdown
    page["images"] = resources["outputs"]
    return page
