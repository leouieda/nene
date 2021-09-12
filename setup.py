"""
Build and install the project.

Project metadata and build configuration is defined in setup.cfg.
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
