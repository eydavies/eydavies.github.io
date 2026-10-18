#!/usr/bin/env python3
"""Build the website.

The pages in the site root (index.html, about.html, ...) and the CV PDF are
GENERATED from the files in src/. To change the site:

    1. edit
         src/layout.html        header/nav/footer shared by every page
         src/pages/*.html       the content of each page
         src/publications.json  the publication list for the Publications page
         src/abstracts.json     abstracts keyed by arXiv ID (optional per paper)
         src/bibtex.json        BibTeX entries keyed by arXiv ID (optional per paper)
         src/cv.tex             your CV, as LaTeX (moderncv, "classic", black)
         src/people.json        supervisor name -> website, linked on the web CV only
    2. run   python3 build.py   from this folder
         (add --no-pdf to skip compiling the CV PDF);
    3. commit and push the regenerated files along with your edits.

The CV: src/cv.tex is the single source. build.py turns its \\section and
\\cventry lines into the interactive CV on resume.html, and compiles the same
file with pdflatex into elliot_davies_cv.pdf (the page's "Download PDF"
button). If pdflatex is not installed, or the compile fails, the existing PDF
is left untouched and a message is printed.

Needs Python 3 (no extra packages) and, for the PDF, a LaTeX install that has
moderncv. Put a custom moderncv.cls / .sty in src/ if you use one.
"""
import argparse
import datetime
import hashlib
import html
import json
import os
import pathlib
import re
import shutil
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / "src"

SITE_URL = "https://eydavies.github.io/"
SITE_NAME = "Elliot Y. Davies"
CV_PDF = "elliot_davies_cv.pdf"          # served by the "Download PDF" button
CV_DOWNLOAD_NAME = "Elliot_Y_Davies_CV.pdf"  # file name the visitor's browser saves

# (page key, output file, label) in the order shown in the navigation bar.
NAV = [
    ("about", "about.html", "About"),
    ("cv", "resume.html", "CV"),
    ("publications", "publics.html", "Publications"),
    ("contact", "contact.html", "Contact"),
    # The Local Group is a separate site (its own repo, served from
    # bostonlocalgroup.space); this tab just links to its home page.
    ("local-group", "https://bostonlocalgroup.space/", "The Local Group"),
]

# Shorter labels for the CV's section-jump chips (the full heading is kept
# on the page itself). Sections not listed here use their own heading.
CV_CHIP_LABELS = {
    "Publication Summary": "Summary",
    "First Author Publications": "First-author papers",
    "Other Publications": "Other papers",
    "Teaching & Supervision": "Teaching",
    "Conferences, Talks & Schools": "Talks",
    "Awards & Academic Programmes": "Awards",
}

WARNINGS = []


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


# ---------------------------------------------------------------------------
# Publications page
# ---------------------------------------------------------------------------

# Loaded on pages whose metadata says `mathjax: true`, so that TeX in abstracts
# (e.g. $(E,L_z)$) is typeset. Without JavaScript the raw TeX stays readable.
MATHJAX = """\t<script>window.MathJax = {tex: {inlineMath: [['$', '$']]}};</script>
\t<script defer src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-chtml.js"></script>"""


def render_abstract(text):
    """Escape an arXiv abstract for HTML, keeping $...$ TeX intact and turning
    the few text-mode TeX commands arXiv abstracts use into HTML."""
    text = html.escape(text, quote=False)
    text = re.sub(r"\\textit\{([^}]*)\}", r"<em>\1</em>", text)
    return text.replace("\\%", "%")


def render_publications():
    pubs = json.loads((SRC / "publications.json").read_text(encoding="utf-8"))
    abstracts = json.loads((SRC / "abstracts.json").read_text(encoding="utf-8"))
    bibtex = json.loads((SRC / "bibtex.json").read_text(encoding="utf-8"))
    sections = []
    for heading, first_author in (("First-author publications", True),
                                  ("Other publications", False)):
        items = [p for p in pubs if p["first_author"] == first_author]
        out = ['\t\t<section class="pub-section">',
               f'\t\t\t<h2>{heading}</h2>']
        for year in sorted({p["year"] for p in items}, reverse=True):
            out.append('\t\t\t<div class="pub-year">')
            out.append(f'\t\t\t\t<h3>{year}</h3>')
            out.append('\t\t\t\t<ul class="pub-list">')
            for p in (p for p in items if p["year"] == year):
                title = html.escape(p["title"])
                venue = html.escape(p["venue"])
                arxiv = html.escape(p["arxiv"])
                button = panel = bib_button = bib_panel = ""
                if p["arxiv"] in bibtex:
                    bid = "bib-" + p["arxiv"].replace(".", "-")
                    bib_button = (f' <button type="button" class="bib-toggle" aria-expanded="false" '
                                  f'aria-controls="{bid}">BibTeX</button>')
                    bib_panel = (f'<div class="pub-bibtex" id="{bid}">'
                                 '<button type="button" class="bib-copy">Copy</button>'
                                 f'<pre><code>{html.escape(bibtex[p["arxiv"]], quote=False)}</code></pre></div>')
                if p["arxiv"] in abstracts:
                    aid = "abs-" + p["arxiv"].replace(".", "-")
                    button = (f'<button type="button" class="abs-toggle" aria-expanded="false" '
                              f'aria-controls="{aid}">Abstract</button>')
                    panel = (f'<div class="pub-abstract" id="{aid}">'
                             f'<p>{render_abstract(abstracts[p["arxiv"]])}</p></div>')
                out.append(
                    '\t\t\t\t\t<li class="pub"><div class="pub-row"><div class="pub-text">'
                    f'<a class="pub-title" href="https://arxiv.org/abs/{arxiv}">{title}</a>'
                    f'<span class="pub-meta">{venue}{bib_button}</span>'
                    f'</div>{button}</div>{bib_panel}{panel}</li>')
            out.append('\t\t\t\t</ul>')
            out.append('\t\t\t</div>')
        out.append('\t\t</section>')
        sections.append("\n".join(out))
    return "\n".join(sections)


# ---------------------------------------------------------------------------
# CV: src/cv.tex -> interactive HTML (+ PDF, see compile_cv_pdf)
# ---------------------------------------------------------------------------

def read_group(s, i):
    """s[i] must be '{'. Return (inner text, index just after the matching '}')."""
    depth = 0
    j = i
    while j < len(s):
        c = s[j]
        if c == "\\":
            j += 2          # skip escaped characters such as \{ \} \\ \&
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
        j += 1
    raise ValueError("unbalanced braces in src/cv.tex")


def strip_tex_comments(tex):
    return "\n".join(re.sub(r"(?<!\\)%.*$", "", line) for line in tex.splitlines())


CV_COMMAND = re.compile(r"\\(section|cventry)(?![A-Za-z])\s*")


def parse_cv(tex):
    """Return [{'title': str, 'entries': [[6 raw args], ...]}, ...]."""
    if r"\begin{document}" not in tex:
        raise ValueError(r"src/cv.tex has no \begin{document}")
    body = tex.split(r"\begin{document}", 1)[1].split(r"\end{document}")[0]
    body = strip_tex_comments(body)
    sections, pos = [], 0
    while True:
        m = CV_COMMAND.search(body, pos)
        if not m:
            break
        name, i, args = m.group(1), m.end(), []
        for _ in range(1 if name == "section" else 6):
            while i < len(body) and body[i].isspace():
                i += 1
            if i >= len(body) or body[i] != "{":
                raise ValueError(f"\\{name} in src/cv.tex is missing an argument "
                                 f"near: {body[m.start():m.start() + 60]!r}")
            arg, i = read_group(body, i)
            args.append(arg)
        pos = i
        if name == "section":
            sections.append({"title": args[0], "entries": []})
        else:
            if not sections:
                raise ValueError(r"\cventry before the first \section in src/cv.tex")
            sections[-1]["entries"].append(args)
    return sections


WRAP_COMMANDS = {"textbf": "strong", "textit": "em", "emph": "em", "textsl": "em",
                 "textsuperscript": "sup", "textsubscript": "sub"}
PLAIN_COMMANDS = {"textrm", "textsf", "texttt", "textnormal", "mbox", "hbox"}
IGNORED_COMMANDS = {"small", "large", "Large", "footnotesize", "normalsize", "par",
                    "newpage", "noindent", "centering", "bfseries", "itshape"}
SYMBOL_COMMANDS = {"ldots": "…", "dots": "…", "textellipsis": "…",
                   "textbackslash": "\\", "TeX": "TeX", "LaTeX": "LaTeX"}
ESCAPED_SYMBOLS = {"&": "&amp;", "%": "%", "_": "_", "$": "$", "#": "#",
                   "{": "{", "}": "}", " ": " ", ",": "\u2009", "-": ""}


def tex_to_html(s):
    """Convert the small LaTeX subset used inside \\cventry arguments to HTML."""
    out, i = [], 0
    while i < len(s):
        c = s[i]
        if c == "\\":
            if s.startswith("\\\\", i):
                out.append("<br>")
                i += 2
                continue
            m = re.match(r"\\([A-Za-z]+)\s*", s[i:])
            if m:
                name = m.group(1)
                i += m.end()
                has_arg = i < len(s) and s[i] == "{"
                if name in WRAP_COMMANDS and has_arg:
                    inner, i = read_group(s, i)
                    tag = WRAP_COMMANDS[name]
                    out.append(f"<{tag}>{tex_to_html(inner)}</{tag}>")
                elif name == "href" and has_arg:
                    url, i = read_group(s, i)
                    text = ""
                    if i < len(s) and s[i] == "{":
                        text, i = read_group(s, i)
                    out.append(f'<a href="{html.escape(url.strip())}">{tex_to_html(text) or html.escape(url)}</a>')
                elif name == "url" and has_arg:
                    url, i = read_group(s, i)
                    out.append(html.escape(url.strip()))   # linkified below
                elif name in PLAIN_COMMANDS and has_arg:
                    inner, i = read_group(s, i)
                    out.append(tex_to_html(inner))
                elif name in SYMBOL_COMMANDS:
                    out.append(SYMBOL_COMMANDS[name])
                elif name in IGNORED_COMMANDS:
                    pass
                else:
                    WARNINGS.append(f"cv.tex: unsupported command \\{name} (shown without formatting)")
                    if has_arg:
                        inner, i = read_group(s, i)
                        out.append(tex_to_html(inner))
                continue
            nxt = s[i + 1] if i + 1 < len(s) else ""
            if nxt in ESCAPED_SYMBOLS:
                out.append(ESCAPED_SYMBOLS[nxt])
            else:
                WARNINGS.append(f"cv.tex: unsupported escape \\{nxt}")
            i += 2
        elif c == "{":
            inner, i = read_group(s, i)
            out.append(tex_to_html(inner))
        elif c == "}":
            i += 1
        elif s.startswith("---", i):
            out.append("—")
            i += 3
        elif s.startswith("--", i):
            out.append("–")
            i += 2
        elif s.startswith("``", i):
            out.append("“")
            i += 2
        elif s.startswith("''", i):
            out.append("”")
            i += 2
        elif c == "~":
            out.append("\u00a0")
            i += 1
        else:
            out.append(html.escape(c, quote=False))
            i += 1
    text = "".join(out)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s*<br>\s*", "<br>", text)
    return re.sub(r"^(<br>)+|(<br>)+$", "", text.strip()).strip()


URL_RE = re.compile(r"(?<![\"'>=/])https?://[^\s<]+")
ORCID_RE = re.compile(r"(?<![\w/])(\d{4}-\d{4}-\d{4}-\d{3}[\dX])(?![\w-])")


def linkify(text):
    def link(m):
        url = m.group(0)
        trail = ""
        while url and url[-1] in ".,;:)":
            trail = url[-1] + trail
            url = url[:-1]
        label = re.sub(r"^https?://(www\.)?", "", url)
        return f'<a href="{url}">{label}</a>{trail}'
    text = URL_RE.sub(link, text)
    return ORCID_RE.sub(r'<a href="https://orcid.org/\1">\1</a>', text)


def slugify(title):
    s = re.sub(r"[^a-z0-9]+", "-", tex_to_html(title).lower().replace("&amp;", " ")).strip("-")
    return s or "section"


# Supervisors / PIs are linked to their websites on the web page only (the PDF
# is compiled from cv.tex, which is left untouched). Names and URLs live in
# src/people.json; names are linked inside these CV sections only, so the same
# people are not linked in publication author lists.
PEOPLE_LINK_SECTIONS = {"Employment", "Education"}


def link_people(text, people):
    for name, url in people.items():
        text = re.sub(rf"(?<![\w>]){re.escape(html.escape(name, quote=False))}(?![\w<])",
                      f'<a href="{html.escape(url)}">{html.escape(name, quote=False)}</a>', text)
    return text


def render_cv_entry(args, people=None):
    date, title, subtitle, place, note, desc = (linkify(tex_to_html(a)) for a in args)
    if people:
        desc = link_people(desc, people)
    parts = []
    if title:
        parts.append(f'<h3 class="cv-title">{title}</h3>')
    if subtitle:
        parts.append(f'<p class="cv-sub">{subtitle}</p>')
    meta = " &middot; ".join(x for x in (place, note) if x)
    if meta:
        parts.append(f'<p class="cv-meta">{meta}</p>')
    if desc:
        parts.append(f'<p class="cv-desc">{desc}</p>')
    date_html = f'<div class="cv-date">{date}</div>' if date else '<div class="cv-date"></div>'
    inner = "\n".join(f"\t\t\t\t\t\t{p}" for p in parts)
    return (f'\t\t\t\t<article class="cv-entry">\n\t\t\t\t\t{date_html}\n'
            f'\t\t\t\t\t<div class="cv-main">\n{inner}\n\t\t\t\t\t</div>\n\t\t\t\t</article>')


def render_cv():
    sections = parse_cv((SRC / "cv.tex").read_text(encoding="utf-8"))
    people = json.loads((SRC / "people.json").read_text(encoding="utf-8"))
    chips, blocks = [], []
    for sec in sections:
        title = tex_to_html(sec["title"])
        sid = slugify(sec["title"])
        label = CV_CHIP_LABELS.get(html.unescape(title), title)
        chips.append(f'<a href="#{sid}">{label}</a>')
        link_set = people if html.unescape(title) in PEOPLE_LINK_SECTIONS else None
        entries = "\n".join(render_cv_entry(e, link_set) for e in sec["entries"])
        blocks.append(
            f'\t\t<section class="cv-section" id="{sid}">\n'
            f'\t\t\t<h2>{title}</h2>\n'
            f'\t\t\t<div class="cv-body" id="{sid}-body">\n{entries}\n\t\t\t</div>\n'
            f'\t\t</section>')
    total = sum(len(s["entries"]) for s in sections)
    print(f"parsed src/cv.tex: {len(sections)} sections, {total} entries")
    chip_html = "\n\t\t\t\t".join(chips)
    return f"""\t\t<div class="cv" data-cv>
\t\t\t<div class="cv-sticky">
\t\t\t\t<div class="cv-toolbar">
\t\t\t\t\t<button type="button" class="btn cv-toggle-all js-only">Collapse all</button>
\t\t\t\t\t<a class="btn btn-primary" href="{CV_PDF}" download="{CV_DOWNLOAD_NAME}">Download PDF</a>
\t\t\t\t</div>
\t\t\t\t<nav class="cv-chips" aria-label="CV sections">
\t\t\t\t{chip_html}
\t\t\t\t</nav>
\t\t\t</div>
{chr(10).join(blocks)}
\t\t</div>"""


def compile_cv_pdf():
    """Compile src/cv.tex with pdflatex and install it as elliot_davies_cv.pdf.
    Returns True on success; on any problem leaves the existing PDF alone."""
    exe = shutil.which("pdflatex")
    if not exe:
        print(f"WARNING: pdflatex not found, so {CV_PDF} was NOT regenerated "
              "(install LaTeX with moderncv, or compile src/cv.tex yourself).")
        return False
    env = dict(os.environ)
    env["TEXINPUTS"] = str(SRC) + os.pathsep + env.get("TEXINPUTS", "")  # local moderncv files win
    with tempfile.TemporaryDirectory() as tmp:
        cmd = [exe, "-interaction=nonstopmode", "-halt-on-error",
               "-output-directory", tmp, str(SRC / "cv.tex")]
        for _ in range(2):   # second pass settles any cross-references
            proc = subprocess.run(cmd, cwd=SRC, env=env, stdin=subprocess.DEVNULL,
                                  capture_output=True, text=True)
            if proc.returncode != 0:
                errors = [l for l in proc.stdout.splitlines() if l.startswith("!")]
                print(f"WARNING: pdflatex failed, so {CV_PDF} was NOT regenerated.")
                for line in (errors or proc.stdout.splitlines()[-8:])[:6]:
                    print("   ", line)
                return False
        shutil.copyfile(pathlib.Path(tmp) / "cv.pdf", ROOT / CV_PDF)
    print(f"compiled src/cv.tex -> {CV_PDF}")
    return True


# ---------------------------------------------------------------------------

def asset(name):
    """URL of a static file with a content hash, so browsers/CDNs never serve a stale copy."""
    path = ROOT / name
    digest = hashlib.md5(path.read_bytes()).hexdigest()[:8] if path.exists() else "0"
    return f"{name}?v={digest}"


def main():
    ap = argparse.ArgumentParser(description="Build the website from src/.")
    ap.add_argument("--no-pdf", action="store_true", help="skip compiling the CV PDF")
    opts = ap.parse_args()

    layout = (SRC / "layout.html").read_text(encoding="utf-8")
    today = datetime.date.today()
    for source in sorted((SRC / "pages").glob("*.html")):
        meta, body = parse_page(source.read_text(encoding="utf-8"))
        if "{{publications}}" in body:
            body = body.replace("{{publications}}", render_publications())
        if "{{cv}}" in body:
            body = body.replace("{{cv}}", render_cv())
        title_tag = meta.get("title_tag") or f"{meta['title']} | {SITE_NAME}"
        values = {
            "title_tag": html.escape(title_tag),
            "description": html.escape(meta["description"], quote=True),
            "page_key": meta["key"],
            "site_name": SITE_NAME,
            "canonical": SITE_URL + ("" if source.name == "index.html" else source.name),
            "css_url": asset("style.css"),
            "js_url": asset("site.js"),
            "nav_items": render_nav(meta["key"]),
            "head_extra": "\n".join(filter(None, [
                MATHJAX if meta.get("mathjax") == "true" else "",
                *(f'\t<script defer src="{asset(s.strip())}"></script>' for s in meta.get("scripts", "").split(",") if s.strip()),
            ])),
            "content": body,
            "year": str(today.year),
            "updated": f"{today.day} {today.strftime('%B %Y')}",
        }
        page = layout
        for name, value in values.items():
            page = page.replace("{{" + name + "}}", value)
        (ROOT / source.name).write_text(page, encoding="utf-8")
        print(f"built {source.name}")

    if not opts.no_pdf:
        compile_cv_pdf()
    for w in sorted(set(WARNINGS)):
        print("WARNING:", w)


if __name__ == "__main__":
    main()
