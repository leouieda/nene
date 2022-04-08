# Copyright (c) 2021 Leonardo Uieda.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT
"""Version string coming from setuptools_scm."""
from . import _version_generated

# Create this in a separate module to avoid circular imports when placed in
# nene/__init__.py
__version__ = f"v{_version_generated.version}"
