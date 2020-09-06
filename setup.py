"""
Build and install the project.

Project metadata and build configuration is defined in setup.cfg.
"""
from setuptools import setup


setup(use_scm_version={"write_to": "nene/_version.py"})
