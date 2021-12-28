# Copyright (c) 2021 Leonardo Uieda.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT
"""
Export the run-time requirements from setup.cfg to a requirement.txt format.

Modified from https://github.com/Unidata/MetPy
"""
import configparser

# Read the setup.cfg
config = configparser.ConfigParser()
config.read("setup.cfg")

print("# Run-time dependencies")
for package in config["options"]["install_requires"].strip().split("\n"):
    print(package.strip())

print("# Extra dependencies")
for section in config["options.extras_require"]:
    for package in config["options.extras_require"][section].strip().split("\n"):
        print(package.strip())
