# Copyright (c) 2021 Leonardo Uieda.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT
"""Load data from source files."""
import base64
import json
import textwrap
from pathlib import Path

import yaml

# For Jupyter notebook support
try:
    import nbformat
except ImportError:
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
    if nbformat is None:
        raise ValueError("Need nbformat to read Jupyter notebook files.")
    identifier = generate_identifier(path)
    page = {
        "id": identifier,
        "type": "ipynb",
        "parent": str(path.parent),
        "source": str(path),
    }
    image_dir = str(path.stem) + "_images"
    image_path_template = str(Path(image_dir) / "cell{cell_index}_image.{extension}")
    images = {}
    text_html_template = '<div class="cell_output text_html">\n{html}\n</div>'
    notebook = nbformat.reads(path.read_text(encoding="utf-8"), as_version=4)
    language = "python"
    # Build the Markdown source from the notebook cells
    markdown = []
    for cell_index, cell in enumerate(notebook.cells):
        # Skip empty cells
        if len(cell["source"].strip()) == 0:
            continue
        # Skip cells tagged for skipping
        if "skip" in cell.metadata.get("tags", []):
            continue
        if cell["cell_type"] in ["markdown", "raw"]:
            markdown.append(cell["source"])
        elif cell["cell_type"] == "code":
            markdown.append(f"```{language}\n{cell['source']}\n```")
            output_pre = []
            output_display = None
            for output in cell["outputs"]:
                if output["output_type"] == "stream":
                    output_pre.append(output["text"])
                elif output["output_type"] == "error":
                    output_pre.append(f"{output['ename']}: {output['evalue']}")
                    traceback = "\n".join(output["traceback"])
                    output_pre.append(f"Traceback:\n{traceback}")
                elif output["output_type"] in ["display_data", "execute_result"]:
                    if "text/html" in output["data"]:
                        html = output["data"]["text/html"]
                        if "<style>" in html:
                            start = html.find("<style>")
                            end = html.find("</style>") + 8
                            css = textwrap.dedent(html[start:end]).replace("\n", " ")
                            html = html[:start] + css + html[end:]
                        output_display = text_html_template.format(html=html)
                    elif "text/plain" in output["data"]:
                        output_pre.append(output["data"]["text/plain"])
                    if output_display is None:
                        for mime_type in output["data"]:
                            main_type, sub_type = mime_type.split("/")
                            if main_type == "image":
                                image_data = base64.b64decode(
                                    output["data"][mime_type].split("base64,")[-1]
                                )
                                image_path = image_path_template.format(
                                    cell_index=cell_index, extension=sub_type
                                )
                                images[image_path] = image_data
                                caption = "Output of the code shown above."
                                output_display = f"![{caption}]({image_path})"
                                break
                else:
                    pass
            if output_pre:
                output_pre = "\n".join(output_pre)
                markdown.append(f"```\n{output_pre}\n```")
            if output_display is not None:
                markdown.append(output_display)
        else:
            pass
    page["markdown"] = "\n\n".join(markdown)
    page["images"] = images
    return page
