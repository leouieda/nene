"""
Command line interface
"""
import sys
from pathlib import Path
import shutil
import json

import myst_parser.main
import yaml
import livereload
import jinja2


def parse_config():
    """
    Get the configuration
    """
    config = {
        "ignore": [],
    }
    with open("config.json") as config_file:
        config.update(json.load(config_file))
    config["ignore"].append("config.json")
    return config


def crawl(root, ignore):
    """
    Crawl the directory for markdown files and files for copying.
    """
    copy = []
    render = []
    for path in root.glob("**/*"):
        if str(path) in ignore or path.parts[0].startswith("_"):
            continue
        if path.suffix == ".md":
            render.append(path)
        else:
            copy.append(path)
    return copy, render


def main():
    """
    Main program
    """
    config = parse_config()
    print("Configuration:\n", config)

    copy, render = crawl(root=Path("."), ignore=config["ignore"])

    output = Path("_build")
    output.mkdir(exist_ok=True)

    if len(sys.argv) > 1 and sys.argv[1] == "serve":
        server = livereload.Server()
        files = copy + render + ["config.json", "_templates"]
        for filename in files:
            server.watch(filename, "nene")
        server.serve(root="_build/", host="localhost", open_url_delay=1)

    jinja_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(["_templates", "."], followlinks=True),
    )

    print("Parsing Markdown files:")
    site = {}
    for path in render:
        print(f"  {str(path)}")
        identifier = str(path.parent / path.stem)
        page = {
            "id": identifier,
            "path": str(path.with_suffix(".html")),
            "source": str(path),
        }
        source = path.read_text()
        front_matter, markdown = source.split("---")[1:]
        page.update(yaml.safe_load(front_matter.strip()))
        page["markdown"] = markdown
        site[identifier] = page

    print("Rendering Markdown:")
    for identifier in site:
        page = site[identifier]
        print(f"  {page['source']}")
        template = jinja_env.get_template(page["source"], parent=".")
        markdown = template.render(page=page, config=config, site=site)
        page["body"] = myst_parser.main.to_html(markdown)

    print("Rendering HTML:")
    rendered_html = {}
    for identifier in site:
        page = site[identifier]
        print(f"  {page['source']}")
        template = jinja_env.get_template(page["template"])
        rendered_html[page["path"]] = template.render(
            page=page, config=config, site=site
        )

    print("Copying directory tree:")
    for path in copy:
        print(f"  {str(path)}")
        destination = output / path
        if path.is_dir():
            destination.mkdir(exist_ok=True)
        else:
            shutil.copyfile(path, destination)

    print("Writing HTML output:")
    for fname in rendered_html:
        destination = output / Path(fname)
        print(f"  {str(destination)}")
        destination.write_text(rendered_html[fname])
