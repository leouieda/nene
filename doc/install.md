---
title: Installing
template: base.html
---

Nēnē is available from [PyPI][pypi] and can be installed with [pip][pip]:

```bash
python -m pip install nene
```

If you want to use [Jupyter notebooks][jupyter], use this instead to also
install the extra dependencies:

```bash
python -m pip install nene[jupyter]
```

A conda-forge package may come in the future (or maybe not).

<div class="callout callout-warning">

<i class="fa fa-exclamation-triangle text-danger" aria-hidden="true"></i>
**WARNING!**
<i class="fa fa-exclamation-triangle text-danger" aria-hidden="true"></i>

You probably want to pin Nēnē to a specific version since I will likely break
compatibility between releases.

</div>

## Dependencies

Required:

* [MyST](https://myst-parser.readthedocs.io/): parsing and converting Markdown
* [Jinja2](https://jinja2docs.readthedocs.io/): templating engine
* [PyYAML](https://pyyaml.org/): parsing YAML files
* [livereload](https://github.com/lepture/python-livereload): serve the website locally
* [click](https://click.palletsprojects.com): building the command line interface
* [rich](https://rich.readthedocs.io/): pretty output of log messages

For Jupyter support:

* [nbformat](https://nbformat.readthedocs.io/)
* [nbconvert](https://nbconvert.readthedocs.io/)

[pypi]: https://pypi.org/project/nene/
[pip]: https://github.com/pypa/pip
[jupyter]: https://jupyter.org/
