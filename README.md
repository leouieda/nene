# Nēnē: A no-frills static site generator

[![Latest release on PyPI](https://img.shields.io/pypi/v/nene.svg?style=flat-square)][pypi]
[![Compatible Python versions](https://img.shields.io/pypi/pyversions/nene.svg?style=flat-square)][pypi]

Static website generators seem to be the favourite pass time of developers
procrastinating on other more important projects.
So of course, I wanted to try making my own!

> *Nēnē* continues the long tradition of naming static site generators built in
> Python after birds (the nēnē is a [goose endemic to Hawai'i][nene-goose]).

## Why build another one?

Mostly because I wanted to experiment with building command-line programs with
[click][click] and [Rich][rich].
But I also wanted something:

* **No-frills:** I don't want fancy built-in templates, blogging frameworks,
  etc. I'm mostly rolling my own templates.
* **Templates have access to the entire content:** Not all generators allow any
  page to have access to the entire website content. Yes this can cause
  problems with memory, but memory is cheap and I need this feature.
* **Allows templates in Markdown:** Using templating constructs in Markdown
  source files is extremely useful. I've only ever seen this in [Urubu][urubu].
* **Reads data from non-Markdown sources:** Most generators only allow data to
  come into templates from Markdown source files. But sometimes data for
  building a page would be more natural coming from JSON/YAML/etc.
  [Eleventy][11ty] has this concept and I want to use it without figuring out
  how to setup Nodejs.

So I figured that it couldn't be that hard to build something with modern
Python tools that had all of these things.
And for once it actually wasn't!

## Installing

Nēnē is available from [PyPI][pypi] and can be installed with [pip][pip]:

```bash
python -m pip install nene
```

A conda-forge package may come in the future (or maybe not).

## Documentation

Currently being created with Nēnē itself to prove I'm not a hypocrite.

## License

Nēnē is free and open-source software distributed under the
[MIT License](LICENSE.txt).

[nene-goose]: https://www.nps.gov/havo/learn/nature/nene.htm
[click]: https://github.com/pallets/click/
[rich]: https://github.com/willmcgugan/rich/
[urubu]: https://github.com/jandecaluwe/urubu
[11ty]: https://github.com/11ty/eleventy
[pypi]: https://pypi.org/project/nene/
[pip]: https://github.com/pypa/pip
