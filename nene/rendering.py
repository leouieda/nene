# Copyright (c) 2021 Leonardo Uieda.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT
"""Render outputs with Jinja templates."""
import os
from pathlib import Path

import jinja2
import markdown_it
import markdown_it.common.utils
import mdit_py_plugins.anchors
import mdit_py_plugins.footnote
import pygments
import pygments.formatters
import pygments.lexers


def filter_relative_to(path, start):
    """
    Return the relative path from 'start' to 'path'.

    Use as a custom Jinja filter.

    Parameters
    ----------
    path : str
        The path that should be converted to relative.
    start : str
        The path to which the output is relative.

    Returns
    -------
    relative : str
        Relative path from 'start' to 'path'.
    """
    return os.path.relpath(path, start=Path(start).parent)


def make_jinja_envs(templates_dir):
    """
    Create the default Jinja environments given the template folder.

    Parameters
    ----------
    templates_dir : str or pathlib.Path
        The path to the templates.

    Returns
    -------
    envs : dict
        The keys are the file types supported as templates and values are the
        corresponding environments used to render the templates for those file
        types.
    """
    envs = {
        "markdown": jinja2.Environment(
            loader=jinja2.FileSystemLoader([str(templates_dir)], followlinks=True),
            extensions=["jinja2.ext.do", "jinja2.ext.loopcontrols"],
        ),
        "html": jinja2.Environment(
            loader=jinja2.FileSystemLoader([str(templates_dir)], followlinks=True),
            extensions=["jinja2.ext.do", "jinja2.ext.loopcontrols"],
        ),
        "latex": jinja2.Environment(
            loader=jinja2.FileSystemLoader([str(templates_dir)], followlinks=True),
            extensions=["jinja2.ext.do", "jinja2.ext.loopcontrols"],
            # Define custom syntax that is compatible with LaTeX
            # Based on jtex by curvenote (MIT license):
            # https://github.com/curvenote/jtex/blob/2778c9fc51cd2cbbe8d4b7deedd637e9dd59f662/jtex/TemplateRenderer.py#L36
            block_start_string=r"[#",
            block_end_string="#]",
            variable_start_string=r"[-",
            variable_end_string="-]",
            line_comment_prefix=r"%%",
            comment_start_string=r"%#",
            comment_end_string="#%",
            trim_blocks=True,
            autoescape=False,
            auto_reload=True,
            keep_trailing_newline=True,
        ),
    }
    for kind in envs:
        envs[kind].filters["relative_to"] = filter_relative_to
    return envs


def make_markdown_parser():
    """
    Create the Markdown-it-py parser object that can generate HTML.

    Returns
    -------
    parser : MarkdownIt
        A Markdown-it-py parser configured with custom rendering rules and
        plugins.
    """
    parser = markdown_it.MarkdownIt(
        "commonmark", {"typographer": True, "highlight": _highlight_code}
    )
    parser.enable(["replacements", "smartquotes"])
    parser.enable("table")
    parser.use(mdit_py_plugins.anchors.anchors_plugin)
    parser.use(mdit_py_plugins.footnote.footnote_plugin)
    # Remove the starting hr from the footnote block. It's ugly and should be
    # handled through CSS by putting a top border on section element.
    parser.add_render_rule("footnote_block_open", _render_footnote_block_open)
    parser.add_render_rule("fence", _render_code)
    return parser


def _render_footnote_block_open(self, tokens, idx, options, env):
    """Render the footnote opening without the hr tag at the start."""
    html = mdit_py_plugins.footnote.index.render_footnote_block_open(
        self, tokens, idx, options, env
    )
    lines = html.split("\n")
    if lines[0].strip().startswith("<hr"):
        lines = lines[1:]
    return "\n".join(lines)


# This code is based on code from a comment on a markdown-it-py issue:
# https://github.com/executablebooks/markdown-it-py/issues/256#issuecomment-2937277893
########################################################################################
def _highlight_code(code, name, attrs):
    """Use pygments to highlight the code."""
    if name == "":
        return None
    lexer = pygments.lexers.get_lexer_by_name(name)
    formatter = pygments.formatters.HtmlFormatter()
    return pygments.highlight(code, lexer, formatter)


def _render_code(self, tokens, idx, options, env):
    """Highlight the code when rendering it."""
    token = tokens[idx]
    info = (
        markdown_it.common.utils.unescapeAll(token.info).strip() if token.info else ""
    )
    langName = info.split(maxsplit=1)[0] if info else ""
    code = (
        f"<pre><code>{markdown_it.common.utils.escapeHtml(token.content)}</code></pre>"
    )
    if options.highlight:
        return options.highlight(token.content, langName, "") or code
    return code


########################################################################################


def markdown_to_html(page, parser):
    """
    Convert the Markdown content of a page to HTML.

    Parameters
    ----------
    page : dict
        Dictionary with the parsed YAML front-matter and Markdown body.
    parser : MarkdownIt
        A Markdown-it-py parser.

    Returns
    -------
    html : str
        The converted HTML.

    """
    html = parser.render(page["markdown"])
    return html


def render_markdown(page, config, site, build, jinja_envs):
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
    jinja_envs
        A dictionary of Jinja2 environments for loading templates.

    Returns
    -------
    markdown : str
        The rendered Markdown content for the page.
    """
    template = jinja_envs["markdown"].from_string(page["markdown"])
    markdown = template.render(page=page, config=config, site=site, build=build)
    return markdown


def render_output(page, config, site, build, jinja_envs):
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
    jinja_envs
        A dictionary of Jinja2 environments for loading templates.

    Returns
    -------
    html : str
        The converted HTML.

    """
    types = {".html": "html", ".tex": "latex"}
    template_type = types[Path(page["template"]).suffix]
    template = jinja_envs[template_type].get_template(page["template"])
    html = template.render(page=page, config=config, site=site, build=build)
    return html
