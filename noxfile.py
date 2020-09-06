"""
Testing and linting configuration.
"""
import nox


@nox.session(venv_backend="conda", python=["3.8"])
def style(session):
    session.conda_install("--file", "env/requirements-style.txt")
    session.run("black", "--check", "nene", "setup.py")
    session.run("flake8", "nene", "setup.py")


@nox.session(venv_backend="conda", python=["3.8", "3.7", "3.6"])
def test(session):
    session.conda_install("--file", "env/requirements.txt")
    session.conda_install("--file", "env/requirements-test.txt")
    session.install("--no-deps", "-e", ".")
    session.run("pytest")
