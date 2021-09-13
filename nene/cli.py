# Copyright (c) 2021 Leonardo Uieda.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT
"""
Defines the command line interface.

Uses click to define a CLI around the ``main`` function.
"""
import shutil
from pathlib import Path

import click
import jinja2
import myst_parser.main
import rich.console

from .core import crawl, load_markdown, parse_config, serve_and_watch

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}
DEFAULT_CONFIG = "config.json"


def make_console(verbose):
    """
    Start up the :class:`rich.console.Console` instance we'll use.

    Parameters
    ----------
    verbose : bool
        Whether or not to print status messages to stderr.
    """
    return rich.console.Console(stderr=True, quiet=not verbose)


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option(
    "--config",
    "-c",
    default=DEFAULT_CONFIG,
    show_default=True,
    help="Specify a different configuration file",
)
@click.option(
    "--serve",
    "-s",
    default=False,
    is_flag=True,
    show_default=True,
    help="Serve the built website and watch for changes (opens your browser)",
)
@click.option(
    "--verbose/--quiet",
    "-v/-q",
    default=True,
    show_default=True,
    help="Print information during execution / Don't print",
)
@click.version_option()
def main(config, serve, verbose):
    """
    Nēnē: A no-frills static site generator.

    Builds a static HTML website from sources, templates, and configuration
    found in the current directory.
    """
    console = make_console(verbose)
    console.print(":building_construction:  [b]Building website...[/b]")

    config_file = config
    config = parse_config(config_file)
    console.print(
        f":package: [b]Loaded configuration from '{config_file}':[/b]", config
    )

    console.print(":open_file_folder: [b]Scanning source directory...[/b]", end=" ")
    tree = crawl(root=Path("."), ignore=config["ignore"], copy_extra=config["copy"])
    console.print("Found:")
    console.print(f"   Markdown files = {len(tree['markdown'])}")
    console.print(f"   JSON files     = {len(tree['json'])}")
    console.print(f"   Other files    = {len(tree['copy'])}")

    output = Path(config["output_dir"])
    output.mkdir(exist_ok=True)

    # Need to add the current dir so we can use the Markdown files as templates
    jinja_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(
            [config["templates_dir"], "."], followlinks=True
        ),
    )

    console.print(":open_book: [b]Reading Markdown files:[/b]")
    site = {}
    for path in tree["markdown"]:
        console.print(f"   {str(path)}")
        page = load_markdown(path)
        site[page["id"]] = page

    console.print(":art: [b]Rendering templates in Markdown files:[/b]")
    for identifier in site:
        page = site[identifier]
        console.print(f"   {page['source']}")
        template = jinja_env.get_template(page["source"], parent=".")
        markdown = template.render(page=page, config=config, site=site)
        page["body"] = myst_parser.main.to_html(markdown)

    console.print(":art: [b]Rendering HTML templates:[/b]")
    rendered_html = {}
    for identifier in site:
        page = site[identifier]
        console.print(f"   {page['path']} ← {page['template']}")
        template = jinja_env.get_template(page["template"])
        rendered_html[page["path"]] = template.render(
            page=page, config=config, site=site
        )

    console.print(
        ":deciduous_tree: [b]Copying source directory tree and extra files to "
        f"'{str(output)}':[/b]"
    )
    for path in tree["copy"]:
        console.print(f"   {str(path)}")
        destination = output / path
        if path.is_dir():
            destination.mkdir(exist_ok=True)
        else:
            shutil.copyfile(path, destination)

    console.print(f":writing_hand:  [b]Writing HTML files to '{str(output)}':[/b]")
    for fname in rendered_html:
        destination = output / Path(fname)
        console.print(f"   {str(destination)}")
        destination.write_text(rendered_html[fname])

    console.print(":rocket: [b]Done![/b] :tada:")

    if serve:
        console.print(
            f":eyes: [b]Serving files in '{config['output_dir']}' and "
            f"watching for changes...[/b]"
        )
        serve_and_watch(
            output,
            config_file,
            watch=tree,
            extra=[config_file, config["templates_dir"]],
            quiet=not verbose,
        )
