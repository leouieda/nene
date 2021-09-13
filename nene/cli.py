"""
Command line interface
"""
from pathlib import Path
import shutil

import myst_parser.main
import jinja2
import rich.console
import click

from .core import crawl, parse_config, serve_and_watch, load_markdown


CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])
DEFAULT_CONFIG = "config.json"


def make_console(verbose):
    """
    Start up the :class:`rich.console.Console` instance we'll use.
    """
    return rich.console.Console(stderr=True, quiet=not verbose)


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option()
def main():
    """
    A no-nonsense static site generator
    """
    pass


@main.command(short_help="Serve the HTML and watch for changes")
@click.option(
    "--verbose/--quiet",
    "-v/-q",
    default=True,
    show_default=True,
    help="Print server log messages / Don't print",
)
def serve(verbose):
    """
    Serve the generated HTML, open a browser, and watch files for changes.

    The HTML is automatically rebuilt and the website reloaded in the browser
    every time a source file is changed.
    """
    config_file = DEFAULT_CONFIG
    config = parse_config(config_file)

    console = make_console(verbose)
    console.print(
        f":eyes: [b]Serving files in '{config['output_dir']}' and "
        f"watching for changes...[/b]"
    )
    console.print(
        f":package: [b]Loaded configuration from '{config_file}':[/b]", config
    )

    tree = crawl(root=Path("."), ignore=config["ignore"])

    output = Path(config["output_dir"])
    output.mkdir(exist_ok=True)

    serve_and_watch(
        output,
        watch=tree,
        extra=[config_file, config["templates_dir"]],
        quiet=not verbose,
    )


@main.command(short_help="Build HTML output")
@click.option(
    "--verbose/--quiet",
    "-v/-q",
    default=True,
    show_default=True,
    help="Print information about the build / Don't print",
)
def build(verbose):
    """
    Build the HTML files from the sources and configuration.

    Output is placed in the "_build" directory.
    """
    console = make_console(verbose)
    console.print(":building_construction:  [b]Building website...[/b]")

    config_file = DEFAULT_CONFIG
    config = parse_config(config_file)
    console.print(
        f":package: [b]Loaded configuration from '{config_file}':[/b]", config
    )

    console.print(":open_file_folder: [b]Scanning source directory...[/b]", end=" ")
    tree = crawl(root=Path("."), ignore=config["ignore"])
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
