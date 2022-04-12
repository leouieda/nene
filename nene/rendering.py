# Copyright (c) 2021 Leonardo Uieda.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT
"""Render outputs with Jinja templates."""
import jinja2
import mdit_py_plugins.anchors
import mdit_py_plugins.footnote
from markdown_it import MarkdownIt


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


def markdown_to_html(page):
    """
    Convert the Markdown content of a page to HTML.

    Parameters
    ----------
    page : dict
        Dictionary with the parsed YAML front-matter and Markdown body.

    Returns
    -------
    html : str
        The converted HTML.

    """
    parser = MarkdownIt("commonmark", {"typographer": True})
    parser.enable(["replacements", "smartquotes"])
    parser.enable("table")
    parser.use(mdit_py_plugins.anchors.anchors_plugin)
    parser.use(mdit_py_plugins.footnote.footnote_plugin)
    # Remove the starting hr from the footnote block. It's ugly and should be
    # handled through CSS by putting a top border on section element.
    parser.add_render_rule("footnote_block_open", _render_footnote_block_open)
    html = parser.render(page["markdown"])
    return html


def _render_footnote_block_open(self, tokens, idx, options, env):
    """Render the footnote opening without the hr tag at the start."""
    html = mdit_py_plugins.footnote.index.render_footnote_block_open(
        self, tokens, idx, options, env
    )
    lines = html.split("\n")
    if lines[0].strip().startswith("<hr"):
        lines = lines[1:]
    return "\n".join(lines)


def render_markdown(page, config, site, build, jinja_env):
    """
    Render the templates in Markdown content of the page.

    Parameters
    ----------
    page : dict
        Dictionary with the parsed YAML front-matter and Markdown body.
    config : dict
        A dictionary with the default configuration and variables loaded from
        the file.
    site : dict
        Dictionary with the entire site content so far.
    build : dict
        Dictionary with information about the build environment.
    jinja_env
        A Jinja2 environment for loading templates.

    Returns
    -------
    markdown : str
        The rendered Markdown content for the page.
    """
    template = jinja_env.from_string(page["markdown"])
    markdown = template.render(page=page, config=config, site=site, build=build)
    return markdown


def render_output(page, config, site, build, jinja_env):
    """
    Render the full template output for a page.

    Parameters
    ----------
    page : dict
        Dictionary with the page metadata and body content (in HTML not just
        Markdown).
    config : dict
        A dictionary with the default configuration and variables loaded from
        the file.
    site : dict
        Dictionary with the entire site content so far.
    build : dict
        Dictionary with information about the build environment.
    jinja_env
        A Jinja2 environment for loading templates.

    Returns
    -------
    html : str
        The converted HTML.

    """
    template = jinja_env.get_template(page["template"])
    html = template.render(page=page, config=config, site=site, build=build)
    return html
