---
title: Nene documetation
template: base.html
---

Some text. **In markdown!**

Templates in the sources? Yes!

Page name: {{ page.title }}

HTML: {{ page.path }}

{%- for name, url in config.menu %}
<li class="nav-item">
  <a class="nav-link" href="{{ url }}">{{ name }}</a>
</li>
{%- endfor %}

Inception:

{{ page.markdown }}
