# Copyright (c) 2021 Leonardo Uieda.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT
"""Render outputs with Jinja templates."""
import jinja2
import myst_parser.main


def make_jinja_env(templates_dir):
    """
    Create the default Jinja environment given the template folder.

    Parameters
    ----------
    templates_dir : str or pathlib.Path
        The path to the templates.

    Returns
    -------
    env : jinja2.Environment
        The environment used to render the templates.
    """
    # Need to add the current dir so we can use the Markdown files as templates
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader([str(templates_dir), "."], followlinks=True),
        extensions=["jinja2.ext.do", "jinja2.ext.loopcontrols"],
    )
    return env


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
