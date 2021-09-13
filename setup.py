# Copyright (c) 2021 Leonardo Uieda.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT
"""
Setup configuration for the Python package.

Metadata and build configuration are defined in setup.cfg.
"""
from setuptools import setup

setup(
    use_scm_version={
        "relative_to": __file__,
        "version_scheme": "post-release",
        "local_scheme": "node-and-date",
        "write_to": "nene/_version.py",
    }
)
