# Copyright (c) 2021 Leonardo Uieda.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT
"""
Defines the command line interface.

Uses click to define a CLI around the ``main`` function.
"""
import logging
import shutil
import sys
from pathlib import Path

import click
import livereload

from .crawling import crawl
from .parsing import load_config, load_data, load_jupyter_notebook, load_markdown
from .printing import make_console, print_dict, print_file_stats
from .rendering import make_jinja_env, markdown_to_html
from .utils import capture_build_info

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}
DEFAULT_CONFIG = "config.yml"


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
    Nene: A no-frills static site generator.

    Builds a static HTML website from sources, templates, and configuration
    found in the current directory.
    """
    config_file = config
    console = make_console(verbose)
    style = "bold blue"
    console.rule(
        ":palm_tree: Lay back and relax while Nēnē builds your website :palm_tree:",
        style=style,
    )
    try:
        output, tree, config = build(config_file, console, style)
    except Exception:
        console_error = make_console(verbose=True)
        style = "bold red"
        console.print()
        console.rule(":fire: Error messages start here :fire:", style=style)
        console.print_exception(suppress=[click])
        console.rule(":fire: Error messages above :fire:", style=style)
        console.print()
        console_error.print(
            ":pensive: Oh no! Something went wrong while building your website.",
            style=style,
        )
        if not verbose:
            console_error.print(
                ":bulb: "
                "You may want to run Nēnē again with verbosity turned on ('--verbose') "
                "to get more information about what happened."
            )
        console.print()
        console.print("A few things to check:", style="bold")
        console.print("  1. The error messages above for clues.")
        console.print("  2. Configuration and data files and Markdown headers.")
        console.print()
        console.print("Can't figure out what is happening?", style="bold")
        console.print(
            "  * Consider submitting a bug report: "
            "https://github.com/leouieda/nene/issues"
        )
        console.print("  * Please include the output above :point_up_2: when doing so.")
        console.print()
        sys.exit(1)
    else:
        console.rule(":rocket: [bold green]Done![/] :tada:", style=style)
        console.print()
        console.print(
            f":gift: Your built website is in '{str(output)}'. Enjoy!",
            style="bold green",
        )

    if serve:
        console.print()
        console.rule(
            f":eyes: Serving files in '{config['output_dir']}' and "
            f"watching for changes in the sources",
            style=style,
        )
        serve_and_watch(
            output,
            config_file,
            watch=tree,
            extra=[config_file, config["templates_dir"]],
            quiet=not verbose,
        )
    sys.exit(0)


def build(config_file, console, style):
    """
    Build the website HTML.

    Main function used to build the website. Reads in data from files,
    converts, renders, etc.

    Parameters
    ----------
    config_file : str
        Path to the configuration file.
    console : rich.console.Console
        The rich Console used to print log messages.
    style : str
        Formatting style used for the main status messages.

    Returns
    -------
    output : pathlib.Path
        Path of the output folder.
    tree : dict
        Dictionary with lists of source files by file type.
    config : dict
        Parameters read from the main configuration file.
    """
    with console.status(f"[{style}]Working...[/{style}]"):
        console.print(
            ":package: Captured information about the build environment:", style=style
        )
        build = capture_build_info()
        print_dict(build, console)

        console.print(
            f":package: Configuration loaded from '{config_file}':", style=style
        )
        config = load_config(config_file)
        print_dict(config, console)

        console.print(":open_file_folder: Scanned source directory:", style=style)
        tree = crawl(root=Path("."), ignore=config["ignore"], copy_extra=config["copy"])
        print_file_stats(tree, console)

        output = Path(config["output_dir"])
        output.mkdir(exist_ok=True)

        jinja_env = make_jinja_env(config["templates_dir"])

        site = {}
        data = {}

        console.print(":open_book: Reading Markdown files:", style=style)
        if tree["markdown"]:
            for path in tree["markdown"]:
                console.print(f"   {str(path)}")
                page = load_markdown(path)
                site[page["id"]] = page
        else:
            console.print("   There weren't any :disappointed:")

        console.print(
            ":open_book: Reading Jupyter Notebook files as Markdown:", style=style
        )
        if tree["ipynb"]:
            for path in tree["ipynb"]:
                console.print(f"   {str(path)}")
                page = load_jupyter_notebook(path)
                site[page["id"]] = page
        else:
            console.print("   There weren't any :disappointed:")

        console.print(":open_book: Reading JSON data files:", style=style)
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

        console.print(":truck: Propagating data through the website:", style=style)
        if data:
            for page in site.values():
                if page["parent"] in data:
                    console.print(f"   {page['source']}:")
                    for datum in data[page["parent"]]:
                        console.print(f"     ↳ {datum['source']}")
                        # Merge the two data dictionaries with 'page' taking precedence
                        page.update({**datum["content"], **page})
        else:
            console.print("   There wasn't any :disappointed:")

        console.print(":butterfly: Transforming Markdown to HTML:", style=style)
        for page in site.values():
            console.print(f"   {page['source']}")
            page["body"] = markdown_to_html(page, jinja_env, config, site, build)

        console.print(":art: Rendering HTML output:", style=style)
        rendered_html = {}
        for page in site.values():
            console.print(f"   {page['path']} ← {page['template']}")
            template = jinja_env.get_template(page["template"])
            rendered_html[page["id"]] = template.render(
                page=page, config=config, site=site, build=build
            )

        console.print(
            ":deciduous_tree: Copying source directory tree and extra files to "
            f"'{str(output)}':",
            style=style,
        )
        for path in tree["copy"]:
            console.print(f"   {str(path)}")
            destination = output / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, destination)

        console.print(
            f":writing_hand:  Writing HTML files to '{str(output)}':", style=style
        )
        for identifier in rendered_html:
            page = site[identifier]
            destination = output / Path(page["path"])
            console.print(f"   {str(destination)} ⇒  id: {page['id']}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(rendered_html[identifier], encoding="utf-8")

        console.print(":bar_chart: Writing Jupyter Notebook image files:", style=style)
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
    return output, tree, config


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
