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
import rich.console

from .core import (
    crawl,
    load_data,
    load_jupyter_notebook,
    load_markdown,
    markdown_to_html,
    parse_config,
    serve_and_watch,
)

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}
DEFAULT_CONFIG = "config.yml"


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
    console.print(f"   Markdown         = {len(tree['markdown'])}")
    console.print(f"   Jupyter notebook = {len(tree['ipynb'])}")
    console.print(f"   YAML             = {len(tree['yaml'])}")
    console.print(f"   JSON             = {len(tree['json'])}")
    console.print(f"   Other            = {len(tree['copy'])}")

    output = Path(config["output_dir"])
    output.mkdir(exist_ok=True)

    # Need to add the current dir so we can use the Markdown files as templates
    jinja_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(
            [config["templates_dir"], "."], followlinks=True
        ),
    )

    site = {}
    data = {}

    console.print(":open_book: [b]Reading Markdown files:[/b]")
    if tree["markdown"]:
        for path in tree["markdown"]:
            console.print(f"   {str(path)}")
            page = load_markdown(path)
            site[page["id"]] = page
    else:
        console.print("   There weren't any :disappointed:")

    console.print(":open_book: [b]Reading Jupyter Notebook files as Markdown:[/b]")
    if tree["ipynb"]:
        for path in tree["ipynb"]:
            console.print(f"   {str(path)}")
            page = load_jupyter_notebook(path)
            site[page["id"]] = page
    else:
        console.print("   There weren't any :disappointed:")

    console.print(":open_book: [b]Reading JSON data files:[/b]")
    if tree["json"] + tree["yaml"]:
        # Organizing data by parent folder makes it easier to apply it later
        for path in sorted(tree["json"] + tree["yaml"]):
            console.print(f"   {str(path)}")
            datum = load_data(path)
            if datum["parent"] not in data:
                data[datum["parent"]] = []
            data[datum["parent"]].append(datum)
    else:
        console.print("   There weren't any :disappointed:")

    console.print(":truck: [b]Propagating data through the website:[/b]")
    if data:
        for page in site.values():
            if page["parent"] in data:
                console.print(f"   {page['source']}:")
                for datum in data[page["parent"]]:
                    console.print(f"     ↳ {datum['source']}")
                    page.update(datum["content"])
    else:
        console.print("   There wasn't any :disappointed:")

    console.print(":butterfly: [b]Transforming Markdown to HTML:[/b]")
    for page in site.values():
        console.print(f"   {page['source']}")
        page["body"] = markdown_to_html(page, jinja_env, config, site)

    console.print(":art: [b]Rendering HTML output:[/b]")
    rendered_html = {}
    for page in site.values():
        console.print(f"   {page['path']} ← {page['template']}")
        template = jinja_env.get_template(page["template"])
        rendered_html[page["id"]] = template.render(page=page, config=config, site=site)

    console.print(
        ":deciduous_tree: [b]Copying source directory tree and extra files to "
        f"'{str(output)}':[/b]"
    )
    for path in tree["copy"]:
        console.print(f"   {str(path)}")
        destination = output / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)

    console.print(f":writing_hand:  [b]Writing HTML files to '{str(output)}':[/b]")
    for identifier in rendered_html:
        page = site[identifier]
        destination = output / Path(page["path"])
        console.print(f"   {str(destination)} ⇒  id: [bold green]{page['id']}[/]")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(rendered_html[identifier])

    console.print(":bar_chart: [b]Writing Jupyter Notebook image files:[/b]")
    if tree["ipynb"]:
        for page in site.values():
            if "images" in page:
                console.print(f"   {page['source']}")
                for image_path, image in page["images"].items():
                    path = output / Path(page["parent"]) / Path(image_path)
                    console.print(f"     ↳ {str(path)}")
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(image)
    else:
        console.print("   There weren't any :disappointed:")

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
