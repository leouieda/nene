# Copyright (c) 2021 Leonardo Uieda.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT
"""
Nēnē: A no-nonsense static site generator.

See:

* nene.cli: the command-line application.
* nene.core: functions for building, parsing, converting, etc.
"""
from . import _version

__version__ = f"v{_version.version}"
