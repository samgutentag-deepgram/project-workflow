#!/usr/bin/env python3
"""Assemble .hub/index.html from template.html, hub.yml, and the authored tiles.

  regenerate.py REPO_DIR [--tiles FILE]

The authored tiles are the one part of the page that needs judgment: what to
link, and whether a target is pending, local, or external. So they are NOT
generated. By default they are lifted verbatim out of the existing
index.html's TILES region, which makes a regenerate safe to run at any time
without losing hand-written tiles. Pass --tiles to replace them.

Everything else is mechanical: the header fields come from hub.yml, the
reference sections from render_board.py, and the Asana banner appears only
when hub.yml has asana.url.
"""
from __future__ import annotations

import argparse
import html
import io
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "..", "template.html")
RENDERER = os.path.join(HERE, "render_board.py")


def scalar(text, key):
    """hub.yml top-level scalars, including the `>` folded form used by lede."""
    m = re.search(r"^%s:\s*>\s*\n((?:^[ \t]+.*\n|^\s*\n)+)" % re.escape(key), text, re.M)
    if m:
        return " ".join(ln.strip() for ln in m.group(1).splitlines() if ln.strip())
    m = re.search(r"^%s:[ \t]*(.+?)[ \t]*$" % re.escape(key), text, re.M)
    return m.group(1).strip().strip('"') if m else ""


def region(s, start, end, body):
    i = s.index(start) + len(start)
    j = s.index(end)
    return s[:i] + "\n" + body + "\n" + s[j:]


def extract_tiles(path):
    if not os.path.exists(path):
        return ""
    s = io.open(path, encoding="utf-8").read()
    try:
        i = s.index("<!-- TILES START -->") + len("<!-- TILES START -->")
        j = s.index("<!-- TILES END -->")
    except ValueError:
        return ""
    tiles = s[i:j]
    # The reference sections are generated and re-appended on every run, so a
    # page that already has them would double them. Cut at the first one.
    k = tiles.find("<h2>Reference: ")
    if k != -1:
        tiles = tiles[:k]
    return tiles.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("--tiles", help="file holding the tiles region; default is to reuse the existing page's")
    args = ap.parse_args()

    hub = os.path.join(args.repo, ".hub")
    yml_path = os.path.join(hub, "hub.yml")
    idx_path = os.path.join(hub, "index.html")
    if not os.path.exists(yml_path):
        raise SystemExit("no %s" % yml_path)
    y = io.open(yml_path, encoding="utf-8").read()

    if args.tiles:
        # a tiles file may be a bare fragment or a whole page with the markers
        tiles = extract_tiles(args.tiles) or io.open(args.tiles, encoding="utf-8").read().strip()
    else:
        tiles = extract_tiles(idx_path)
    if not tiles:
        raise SystemExit("no tiles found; pass --tiles")

    ref = subprocess.run([sys.executable, RENDERER, yml_path, "reference"],
                         capture_output=True, text=True, check=True).stdout.strip()

    t = io.open(TEMPLATE, encoding="utf-8").read()
    title = scalar(y, "title") or os.path.basename(os.path.abspath(args.repo))
    e = html.escape
    t = t.replace("<title>PROJECT &middot; Project Hub</title>",
                  "<title>%s &middot; Project Hub</title>" % e(title))
    t = t.replace('<p class="eyebrow"><span class="dg">ORG</span> &middot; WHAT THIS IS &middot; project hub</p>',
                  '<p class="eyebrow"><span class="dg">%s</span> &middot; %s &middot; project hub</p>'
                  % (e(scalar(y, "wordmark")), e(scalar(y, "eyebrow"))))
    t = t.replace("<h1>PROJECT &middot; Project Hub</h1>",
                  "<h1>%s &middot; Project Hub</h1>" % e(title))
    t = t.replace('<p class="lede">One line on what this is and where to start.</p>',
                  '<p class="lede">%s</p>' % e(scalar(y, "lede")))

    # The banner is filled only when hub.yml carries a real URL. A malformed or
    # missing value removes the block outright rather than leaving a placeholder,
    # because a dead "Tracked in Asana" link is worse than no link.
    url = ""
    # a trailing comment after the key is common in these files, so the block
    # matcher must not anchor to end-of-line straight after the colon
    m = re.search(r"^asana:[ \t]*(?:#.*)?\n(?:(?:^[ \t]+.*)?\n)*?(?=^\S|\Z)", y, re.M)
    if m:
        u = re.search(r"^[ \t]+url:[ \t]*(\S+)", m.group(0), re.M)
        if u and u.group(1).startswith("http"):
            url = u.group(1)
    banner = ('<a class="board-link" href="%s" target="_blank" rel="noopener">\n'
              '  <span class="k">Tracked in Asana</span>\n'
              '  <span class="v">%s</span>\n</a>' % (e(url, quote=True), e(title))) if url else ""
    t = region(t, "<!-- BOARD LINK START -->", "<!-- BOARD LINK END -->", banner)
    t = region(t, "<!-- TILES START -->", "<!-- TILES END -->", tiles + ("\n\n" + ref if ref else ""))

    t = re.sub(r'Generated YYYY-MM-DD\.', "Generated %s." % args_date(), t)

    for leftover in ("PROJECT &middot;", "ASANA_URL", "YYYY-MM-DD"):
        assert leftover not in t, "template placeholder survived: %s" % leftover
    io.open(idx_path, "w", encoding="utf-8").write(t)
    print("%-34s %d tiles, %s" % (os.path.basename(os.path.abspath(args.repo)),
                                  t.count('class="tile'),
                                  "Asana banner" if url else "no Asana banner"))


def args_date():
    # Passed in by the caller's environment so the script has no clock of its own
    # and a regenerate is reproducible.
    return os.environ.get("HUB_DATE", "unknown date")


if __name__ == "__main__":
    main()
