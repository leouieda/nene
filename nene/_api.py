# Copyright (c) 2021 Leonardo Uieda.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT
"""Public functions used for building and serving the website."""
import itertools
import logging
import shutil
from pathlib import Path

import livereload

from .crawling import crawl
from .parsing import load_config, load_data, load_jupyter_notebook, load_markdown
from .printing import make_console, print_dict, print_file_stats
from .rendering import (
    make_jinja_envs,
    make_markdown_parser,
    markdown_to_html,
    render_markdown,
    render_output,
)
from .utils import capture_build_info


def build(config_file, console=None, style=""):
    """
    Build the website structure from the sources.

    Reads in configuration, page sources, and data sources. Structures the
    content into dictionaries and prepares the website for rendering.

    Parameters
    ----------
    config_file : str
        Path to the configuration file.
    console : rich.console.Console
        Console used to print status messaged. If None, no messages are
        printed.
    style : str
        Style string used to format console status messages.

    Returns
    -------
    site : dict
        The generated website as a dictionary of pages. Each page has a unique
        ID (usually the relative file path without extension) and is a
        dictionary.
    source_files : dict
        Dictionary with lists of source files by file type.
    config : dict
        Parameters read from the main configuration file.
    build: dict
        Information about the current build (version of Nēnē, git commit, date,
        etc).
    """
    if console is None:
        console, style = make_console(verbose=False)

    console.print(
        ":package: Captured information about the build environment:", style=style
    )
    build_info = capture_build_info()
    print_dict(build_info, console)

    console.print(f":package: Configuration loaded from '{config_file}':", style=style)
    config = load_config(config_file)
    print_dict(config, console)

    console.print(":open_file_folder: Scanned source directory:", style=style)
    source_files = crawl(
        root=Path("."), ignore=config["ignore"], copy_extra=config["copy"]
    )
    print_file_stats(source_files, console)

    site = {}

    console.print(":open_book: Reading Markdown files:", style=style)
    if source_files["markdown"]:
        for path in source_files["markdown"]:
            console.print(f"   {str(path)}")
            page = load_markdown(path)
            site[page["id"]] = page
    else:
        console.print("   None found.")

    console.print(
        ":open_book: Reading Jupyter Notebook files as Markdown:", style=style
    )
    if source_files["ipynb"]:
        for path in source_files["ipynb"]:
            console.print(f"   {str(path)}")
            page = load_jupyter_notebook(path)
            site[page["id"]] = page
    else:
        console.print("   None found.")

    console.print(
        ":open_book: Reading data files and propagating to pages:", style=style
    )
    data_files = source_files["json"] + source_files["yaml"] + source_files["bibtex"]
    if data_files:
        for path in sorted(data_files):
            console.print(f"   {str(path)}")
            data = load_data(path)
            if data["id"] in site and not data["id"].endswith("/index"):
                propagate_to_page = [site[data["id"]]]
            else:
                propagate_to_page = [
                    page for page in site.values() if page["parent"] == data["parent"]
                ]
            for page in propagate_to_page:
                console.print(f"     ↳ {page['id']}")
                if data["id"].endswith("/index") or page["id"] == data["id"]:
                    # Merge the two data dictionaries with 'page' taking precedence
                    page.update({**data["content"], **page})
                else:
                    page[data["id"].split("/")[-1]] = data["content"]
    else:
        console.print("   None found.")

    def pretty_links(source, config):
        """Whether or not this page link should be prettyfied."""
        activated = "pretty_links" in config and config["pretty_links"]
        valid_page = not source.endswith("index.md") and source != "404.md"
        return activated and valid_page

    console.print(":dart: Determining destination path for pages:", style=style)
    for page in site.values():
        if "save_as" in page:
            destination = Path(page["source"]).with_name(page["save_as"])
        elif pretty_links(page["source"], config):
            destination = Path(page["id"]) / "index.html"
        else:
            destination = Path(page["source"]).with_suffix(".html")
        page["path"] = str(destination)
        console.print(f"   {page['id']} ⇒ {page['path']}")

    def get_parent(item):
        """Return the name of the parent of a page for the groupby."""
        page = item[1]
        return page["parent"]

    console.print(":baby: Adding information on sibling pages:", style=style)
    grouped = itertools.groupby(sorted(site.items(), key=get_parent), key=get_parent)
    for parent, group in grouped:
        if parent == ".":
            console.print("   . (base)")
        else:
            console.print(f"   {parent}")
        # The groups are also (key, value) pairs like dict.items().
        siblings = {key for key, value in group}
        for page_id in siblings:
            console.print(f"     ↳ {page_id}")
            site[page_id]["siblings"] = [site[i] for i in (siblings - {page_id})]

    return site, source_files, config, build_info


def render(site, config, build, console=None, style=""):
    """
    Render the HTML or other outputs from the assembled website sources.

    The ``site``, ``config``, and ``build`` variables are passed to the Jinja2
    template for rendering the final outputs.

    Modifies the pages in ``site`` **in place** to add the rendered output of
    each page.

    Parameters
    ----------
    site : dict
        The generated website as a dictionary of pages. Each page has a unique
        ID (usually the relative file path without extension) and is a
        dictionary. The rendered output of each page is added to
        ``page["output"]`` **in place**..
    config : dict
        Parameters read from the main configuration file.
    build: dict
        Information about the current build (version of Nēnē, git commit, date,
        etc).
    console : rich.console.Console
        Console used to print status messaged. If None, no messages are
        printed.
    style : str
        Style string used to format console status messages.
    """
    if console is None:
        console, style = make_console(verbose=False)

    jinja_envs = make_jinja_envs(config["templates_dir"])

    console.print(":art: Rendering templates in Markdown content:", style=style)
    for page in site.values():
        console.print(f"   {page['source']}")
        page["markdown"] = render_markdown(page, config, site, build, jinja_envs)

    parser = make_markdown_parser()

    console.print(":art: Converting Markdown content to HTML:", style=style)
    for page in site.values():
        if "markdown" in page:
            console.print(f"   {page['source']}")
            page["body"] = markdown_to_html(page, parser)

    console.print(":art: Rendering templates for final outputs:", style=style)
    for page in site.values():
        console.print(f"   {page['path']} ← {page['template']}")
        page["output"] = render_output(page, config, site, build, jinja_envs)


def export(site, files_to_copy, output_dir, console=None, style=""):
    """
    Write the output (HTML) and other website files to disk.

    To be used after running ``build``.

    Parameters
    ----------
    site : dict
        The generated website as a dictionary of pages.
    files_to_copy : list
        List of paths to files that need to be copied to the output folder.
    output_dir : str or pathlib.Path
        Path of the output folder.
    console : rich.console.Console
        Console used to print status messaged. If None, no messages are
        printed.
    style : str
        Style string used to format console status messages.
    """
    if console is None:
        console, style = make_console(verbose=False)

    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    console.print(
        ":deciduous_tree: Copying source directory tree and extra files to "
        f"'{str(output_dir)}':",
        style=style,
    )
    for path in files_to_copy:
        console.print(f"   {str(path)}")
        destination = output_dir / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)

    console.print(
        f":writing_hand:  Writing output files to '{str(output_dir)}':", style=style
    )
    for page in site.values():
        destination = output_dir / Path(page["path"])
        console.print(f"   {str(destination)} ⇒  id: {page['id']}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(page["output"], encoding="utf-8")

    console.print(":bar_chart: Writing Jupyter Notebook image files:", style=style)
    pages_with_images = [
        page
        for page in site.values()
        if "images" in page and page["images"] is not None
    ]
    if pages_with_images:
        for page in pages_with_images:
            console.print(f"   {page['source']}")
            for image_path, image in page["images"].items():
                path = output_dir / Path(page["path"]).parent / Path(image_path)
                console.print(f"     ↳ {str(path)}")
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(image)
    else:
        console.print("   None found.")

    console.print(
        f":gift: Your built website is in '{str(output_dir)}'. Enjoy!",
        style=style,
    )


def serve(config, source_files, port=None, console=None, style=""):
    """
    Serve the output folder with livereload and watch the sources for changes.

    When any of the source files are changed, the website is rebuilt
    automatically.

    Parameters
    ----------
    config : dict
        Parameters read from the main configuration file.
    source_files : dict
        Dictionary with lists of source files by file type.
    port : int
        The port used by the server. If None, will first try port 5500 and
        increase by 1 if the port is already busy (maximum of 10 times).
    console : rich.console.Console
        Console used to print status messaged. If None, no messages are
        printed.
    style : str
        Style string used to format console status messages.
    """
    # Note: Can't really quite the livereload server since it sets the logging
    # level and handler when "serve" is called. So we can't set it before
    # anything happens. See livereload/server.py line 331 (as of 2022-04-08).
    livereload_logger = logging.getLogger("livereload")
    if console is None:
        console, style = make_console(verbose=False)

    config_file = config["config_file"]
    watch = [config_file, config["templates_dir"]]
    for category in source_files:
        watch.extend(source_files[category])
    # Make all paths into strings to avoid "JSON serialization errors" coming
    # from livereload
    watch = sorted([str(fname) for fname in watch])

    def rebuild():
        """Rebuild the website."""
        site, source_files, config, build_info = build(config_file)
        render(site, config, build_info)
        export(site, source_files["copy"], config["output_dir"])

    console.print(":eyes: Watching these source files for changes:", style=style)
    server = livereload.Server()
    for fname in watch:
        console.print(f"   {fname}")
        server.watch(fname, rebuild)

    if port is None:
        max_attempts = 10
        port = 5500
    else:
        max_attempts = 1
    for attempt in range(max_attempts):
        console.print(":ledger: Server log messages:", style=style)
        try:
            server.serve(
                root=str(config["output_dir"]),
                host="localhost",
                port=port,
                open_url_delay=1,
            )
            break
        except OSError:
            if attempt == max_attempts + 1:
                raise
            console.print(
                "   Failed to start server because "
                f"port {port} is already in use. "
                "Trying another port."
            )
            port += 1
            # Clear the logger to avoid having livereload duplicate the
            # handlers causing multiple prints of the same log messages.
            livereload_logger.handlers.clear()
