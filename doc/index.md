---
custom_page_title: "Nēnē: A no-frills static site generator"
exclude_h1: true
template: base.html
---

<div class="row mb-3 align-items-center">
<div class="col-md-9 col-sm-8 col-8">

# {{ page.custom_page_title }}

<p class="lead">
Do you love <a href="https://github.com/getpelican">Pelican</a>?
Can't get enough of that <a href="https://jekyllrb.com/">Jekyll</a>?
Then Nēnē is probably not for you.
</p>

</div>
<div class="col-md-3 col-sm-4 col-4">
  <img alt="Nēnē logo" src="/{{ config.logo }}">
</div>
</div>

When I say *no-frills*, I mean it. Nēnē has no built-in templates, no special
provisions for blogging, plugins, or the sort of thing that would be useful if
you just want to start a website.
But it also tries to combine several nice features from other generators into
something that will appeal to those who want to build their own templates.

<div class="callout">

**Trivia:** *Nēnē* continues the long tradition of naming static site
generators built in Python after birds (the nēnē is a [goose endemic to
Hawai'i][nene-goose]).

</div>

## Why build another one?

Static website generators seem to be the favourite pastime of developers
procrastinating on other more important projects.
So of course, I needed to try making my own!
I also wanted to learn how to build command-line programs with [click][click]
and [Rich][rich], so this seemed the perfect side project.

## What Nēnē has to offer

Nēnē was designed to embody several features that I like from different static
site generators:

* **No-frills:** There are no fancy built-in templates, blogging support, RSS
  feeds, etc. You have to roll your own templates.
* **No assumptions about site layout:** The layout of the source files is the
  layout of the output HTML. Source files are converted to HTML, everything
  else is copied directly. It's that simple.
* **Templates have access to the entire content:** Not all generators allow any
  page to have access to the entire website content. This is great for building
  summary pages, lists of entries from across the site, etc.
* **Templates in Markdown files:** Using templating constructs in Markdown
  source files is extremely useful. I've only ever seen this in [Urubu][urubu].
* **Reads data from non-Markdown sources:** Most generators only allow data to
  come into templates from Markdown source files (body and YAML front matter).
  But sometimes data for building a page would be more natural coming from
  an external JSON/YAML/etc. [Eleventy][11ty] has this concept and now you can
  use it without first figuring out how to setup Nodejs.
* **Jupyter support:** Pages can be generated from
  [Jupyter notebooks][jupyter] (no execution) automatically.

## Free and open-source

Nēnē is free and open-source software distributed under the
[MIT License][license].

[nene-goose]: https://www.nps.gov/havo/learn/nature/nene.htm
[click]: https://github.com/pallets/click/
[rich]: https://github.com/willmcgugan/rich/
[urubu]: https://github.com/jandecaluwe/urubu
[11ty]: https://github.com/11ty/eleventy
[license]: https://github.com/leouieda/nene/blob/main/LICENSE.txt
[jupyter]: https://jupyter.org/
