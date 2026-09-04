#!/usr/bin/env python3
"""Render hub.yml's reference groups into the HTML fragment index.html needs.
Mechanical transform only: it decides nothing.

The objectives board this also used to render was removed on 2026-08-26:
all project tracking moved to Asana, because a board in a gitignored local
HTML file is visible to one person and tracking exists so others can see it.

Deliberately a hand-rolled parser for the narrow subset hub.yml uses, because
pyyaml is not installed on this machine and a stdlib-only script is one less
thing that can be missing when a hub is regenerated on a fresh clone.

  render_board.py HUB_YML reference   -> the reference tile sections
"""
from __future__ import annotations

import html
import io
import re
import sys

def inline(s):
    """Escape, then restore the only two markups hub.yml prose uses."""
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)


def parse_reference(text):
    groups, lines, i, inside = [], text.splitlines(), 0, False
    while i < len(lines):
        ln = lines[i]
        if re.match(r"^reference:\s*$", ln):
            inside = True
            i += 1
            continue
        if inside and re.match(r"^\S", ln):
            break
        gm = re.match(r"^  ([^#\s][^:]*):\s*$", ln)
        if inside and gm:
            group, items = gm.group(1), []
            i += 1
            while i < len(lines) and not re.match(r"^  [^#\s][^:]*:\s*$", lines[i]) and not re.match(r"^\S", lines[i]):
                nm = re.match(r"^    - name:\s*(.+?)\s*$", lines[i])
                if nm:
                    entry = {"name": nm.group(1)}
                    i += 1
                    while i < len(lines) and re.match(r"^      \w+:", lines[i]):
                        k, v = lines[i].strip().split(":", 1)
                        entry[k] = v.strip().strip('"')
                        i += 1
                    items.append(entry)
                    continue
                i += 1
            groups.append((group, items))
            continue
        i += 1
    return groups


def render_reference(groups):
    out = []
    for group, items in groups:
        tiles = []
        for it in items:
            url = it.get("url", "")
            # external links get the arrow; a missing local target is not this
            # script's call to make, so unresolved paths render unmarked.
            ext = url.startswith("http")
            cls = "tile ext" if ext else "tile"
            # The hub is opened from a file:// URL in a tab the user closes and
            # reopens. A same-tab navigation to an external site does not just
            # leave the page, it loses it.
            tgt = ' target="_blank" rel="noopener"' if ext else ""
            tiles.append(
                '  <a class="%s" href="%s"%s><span class="name">%s</span>'
                '<span class="desc">%s</span></a>'
                % (cls, html.escape(url, quote=True), tgt, inline(it["name"]), inline(it.get("desc", "")))
            )
        out.append(
            "<h2>Reference: %s</h2>\n<div class=\"grid\">\n%s\n</div>" % (inline(group), "\n".join(tiles))
        )
    return "\n\n".join(out)


def main():
    text = io.open(sys.argv[1], encoding="utf-8").read()
    if sys.argv[2] != "reference":
        raise SystemExit("only mode is 'reference'")
    print(render_reference(parse_reference(text)))


if __name__ == "__main__":
    main()
