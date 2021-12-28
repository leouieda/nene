# Copyright (c) 2021 Leonardo Uieda.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT
"""
Convert the requirements in the given file to their oldest version.

Basically replaces >= with == in place.
"""
import sys

requirements_file = sys.argv[1]


def to_oldest(package):
    """
    Convert the specification to pin to the oldest version.

    Takes the package specification string and replaces the >= with ==.
    """
    oldest = package.split(",")[0].replace(">=", "==")
    return f"{oldest.strip()}\n"


with open(requirements_file) as input_file:
    requirements = [to_oldest(line) for line in input_file]

with open(requirements_file, "wt") as output_file:
    output_file.writelines(requirements)
