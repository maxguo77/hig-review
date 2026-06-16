#!/usr/bin/env python3
"""
Online HIG fetch (single page) — used by the ONLINE review mode.
================================================================

Fetches the *current* guidance for one HIG page straight from Apple, so an
online review can cite guidance newer than the bundled offline corpus.

Usage:
    python hig_fetch.py buttons
    python hig_fetch.py foundations/layout
    python hig_fetch.py https://developer.apple.com/design/human-interface-guidelines/typography
    python hig_fetch.py --json color          # machine-readable output

Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import sys

import hig_lib as hig


def render_text(page: dict) -> str:
    out = [f"# {page['title']}  (ONLINE)",
           f"source: {page['url']}",
           f"platforms: {', '.join(page['platforms'])}",
           ""]
    if page["abstract"]:
        out.append(page["abstract"] + "\n")
    for sec in page["sections"]:
        if sec["heading"] and sec["heading"].lower() != "overview":
            out.append(f"## {sec['heading']}")
        for para in sec["paragraphs"]:
            out.append(f"  {para}")
        for r in sec["rules"]:
            line = f"  - {r['guideline']}"
            if r["explanation"]:
                line += f" {r['explanation']}"
            out.append(line)
        out.append("")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="Fetch current guidance for one HIG page.")
    ap.add_argument("page", help="HIG page slug, path, or full URL (e.g. 'buttons')")
    ap.add_argument("--json", action="store_true", help="emit normalized JSON")
    args = ap.parse_args()

    path = hig.normalize_path(args.page)
    data = hig.fetch_page_json(path)
    if data is None:
        print(f"ERROR: could not fetch HIG page '{args.page}' ({hig.web_url(path)}). "
              f"Check the slug or your network connection.", file=sys.stderr)
        return 1

    page = hig.extract_page(data, path)
    if args.json:
        print(json.dumps(page, ensure_ascii=False, indent=2))
    else:
        print(render_text(page))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
