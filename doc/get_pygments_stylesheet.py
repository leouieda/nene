# Copyright (c) 2021 Leonardo Uieda.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT
"""Generate a pygments CSS stylesheet."""

import pathlib

import pygments.formatters

css = pygments.formatters.HtmlFormatter(style="default").get_style_defs(".highlight")
output = pathlib.Path("css") / "pygments.css"
output.write_text(css)
