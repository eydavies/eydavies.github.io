#!/usr/bin/env python3
"""Build the website.

The pages in the site root (index.html, about.html, ...) are GENERATED from
the files in src/. To change the site:

    1. edit src/layout.html (header/nav/footer shared by every page),
       src/pages/*.html (the content of each page), or
       src/publications.json (the publication list);
    2. run   python3 build.py   from this folder;
    3. commit and push the regenerated HTML files along with your edits.

Needs only Python 3 (no extra packages).
"""
import datetime
import html
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / "src"

SITE_NAME = "Elliot Y. Davies"

# (page key, output file, label) in the order shown in the navigation bar.
NAV = [
    ("about", "about.html", "About"),
    ("cv", "resume.html", "CV"),
    ("publications", "publics.html", "Publications"),
    ("contact", "contact.html", "Contact"),
]


def parse_page(text):
    """Split a page source into (metadata dict, body). Metadata is `key: value`
    lines above a line containing only `---`."""
    head, sep, body = text.partition("\n---\n")
    if not sep:
        raise ValueError("page is missing a '---' line after its metadata")
    meta = {}
    for line in head.strip().splitlines():
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    return meta, body.strip("\n")


def render_nav(active):
    items = []
    for key, href, label in NAV:
        current = ' aria-current="page"' if key == active else ""
        items.append(f'\t\t\t\t<li><a href="{href}"{current}>{label}</a></li>')
    return "\n".join(items)


def render_publications():
    pubs = json.loads((SRC / "publications.json").read_text(encoding="utf-8"))
    sections = []
    for heading, first_author in (("First-author publications", True),
                                  ("Other publications", False)):
        items = [p for p in pubs if p["first_author"] == first_author]
        out = [f'\t\t<section class="pub-section">',
               f'\t\t\t<h2>{heading}</h2>']
        for year in sorted({p["year"] for p in items}, reverse=True):
            out.append('\t\t\t<div class="pub-year">')
            out.append(f'\t\t\t\t<h3>{year}</h3>')
            out.append('\t\t\t\t<ul class="pub-list">')
            for p in (p for p in items if p["year"] == year):
                title = html.escape(p["title"])
                venue = html.escape(p["venue"])
                arxiv = html.escape(p["arxiv"])
                out.append(
                    '\t\t\t\t\t<li>'
                    f'<a class="pub-title" href="https://arxiv.org/abs/{arxiv}">{title}</a>'
                    f'<span class="pub-meta">{venue} &middot; arXiv:{arxiv}</span>'
                    '</li>')
            out.append('\t\t\t\t</ul>')
            out.append('\t\t\t</div>')
        out.append('\t\t</section>')
        sections.append("\n".join(out))
    return "\n".join(sections)


def main():
    layout = (SRC / "layout.html").read_text(encoding="utf-8")
    today = datetime.date.today()
    for source in sorted((SRC / "pages").glob("*.html")):
        meta, body = parse_page(source.read_text(encoding="utf-8"))
        body = body.replace("{{publications}}", render_publications())
        title_tag = meta.get("title_tag") or f"{meta['title']} | {SITE_NAME}"
        values = {
            "title_tag": html.escape(title_tag),
            "description": html.escape(meta["description"], quote=True),
            "page_key": meta["key"],
            "site_name": SITE_NAME,
            "nav_items": render_nav(meta["key"]),
            "content": body,
            "year": str(today.year),
            "updated": f"{today.day} {today.strftime('%B %Y')}",
        }
        page = layout
        for name, value in values.items():
            page = page.replace("{{" + name + "}}", value)
        (ROOT / source.name).write_text(page, encoding="utf-8")
        print(f"built {source.name}")


if __name__ == "__main__":
    main()
