# Copyright (c) 2021 Leonardo Uieda.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT
"""Trying out the API to build the site with a script instead of the CLI."""
import nene

site, source_files, config = nene.build("config.yml")
nene.export(site, source_files["copy"], output_dir=config["output_dir"])
nene.serve(config, source_files)
