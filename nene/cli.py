# Copyright (c) 2021 Leonardo Uieda.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT
"""The Click command line interface ("main" function)."""
import sys

import click

from . import _api
from .printing import make_console

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
    console, style = make_console(verbose)
    style_rule = "green"
    console.rule(
        f":palm_tree: [{style_rule}]Lay back and relax while Nēnē builds "
        "your website[/] :palm_tree:",
        style=style,
    )
    # Main website building section
    try:
        with console.status(f"[{style}]Working...[/{style}]"):
            site, source_files, config, build = _api.build(config_file, console, style)
            _api.render(site, config, build, console, style)
            _api.export(
                site, source_files["copy"], config["output_dir"], console, style
            )
    # Handle exceptions nicely when they occur
    except Exception:
        console_error, style_error = make_console(verbose=True, style="bold red")
        console.print()
        console.rule(":fire: Error messages start here :fire:", style=style_error)
        console.print_exception(suppress=[click])
        console.rule(":fire: Error messages above :fire:", style=style_error)
        console.print()
        console_error.print(
            ":pensive: Oh no! Something went wrong while building your website.",
            style=style_error,
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
        if not serve:
            console.rule(f":tada: [{style_rule}]Done![/] :tada:", style=style)
    # Start the livereload server is requested
    if serve:
        console.rule(
            f":robot: [{style_rule}]Starting development server[/] :robot:",
            style=style,
        )
        _api.serve(
            config,
            source_files,
            console=console,
            style=style,
        )
    sys.exit(0)
