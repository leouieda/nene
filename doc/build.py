# Copyright (c) 2021 Leonardo Uieda.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT
"""Trying out the API to build the site with a script instead of the CLI."""
import sys

import nene

if __name__ == "__main__":
    # Create a Rich Console for printing status updates. To omit the messages,
    # don't pass the console and style to the functions below.
    console, style = nene.printing.make_console(verbose=True)
    # So we know that we're using this script and not the "nene" app.
    console.rule()
    console.print(":snake: Building from the 'build.py' Python script.", style=style)
    console.rule()

    # Generate the website structure based on the YAML configuration file.
    site, source_files, config, build = nene.build(
        "config.yml", console=console, style=style
    )
    # Render the HTML for the website.
    nene.render(site, config, build, console=console, style=style)
    # Export the rendered website to files (including everything that needs to
    # be copied over).
    nene.export(
        site, source_files["copy"], config["output_dir"], console=console, style=style
    )
    # If the script is called with the "-s" command line option, serve the
    # website and open it in a browser.
    if "-s" in sys.argv:
        nene.serve(config, source_files, console=console, style=style)
