#!/usr/bin/env python3
"""
Build / upgrade the offline HIG rules corpus.
=============================================

Crawls every Apple Human Interface Guidelines page (BFS over the DocC JSON
``references`` graph, starting at the HIG root) and writes one rule file per
page into ``rules/pages/<slug>.md`` with structured frontmatter. Also writes a
``rules/manifest.json`` (version, build date, per-page content hash) and a
``rules/index.json`` (rule_set_id -> {title, url, platforms, file, category}).

Usage:
    python build_rules.py            # initialize / regenerate the corpus
    python build_rules.py --upgrade  # re-crawl, diff vs manifest, report changes
    python build_rules.py --limit 20 # cap pages (useful for a quick smoke test)

Stdlib only — see hig_lib.py for the rationale.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import re
import sys
import time
from collections import deque
from pathlib import Path

import hig_lib as hig

SKILL_ROOT = Path(__file__).resolve().parent.parent
RULES_DIR = SKILL_ROOT / "rules"
PAGES_DIR = RULES_DIR / "pages"
MANIFEST = RULES_DIR / "manifest.json"
INDEX = RULES_DIR / "index.json"
VERSION_FILE = SKILL_ROOT / "VERSION"

CRAWL_DELAY_SECONDS = 0.4  # be polite to developer.apple.com


def rule_set_id(path: str) -> str:
    slug = path or "root"
    return "HIG-" + re.sub(r"[^A-Z0-9]+", "-", slug.upper()).strip("-")


def category_of(path: str) -> str:
    """Top-level grouping derived from the page slug, for the index only."""
    if not path:
        return "root"
    if path.startswith("designing-for-"):
        return "platforms"
    head = path.split("/")[0]
    return head


def content_hash(page: dict) -> str:
    payload = json.dumps(
        {
            "title": page["title"],
            "abstract": page["abstract"],
            "platforms": page["platforms"],
            "sections": page["sections"],
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def render_markdown(page: dict, rid: str, fetched: str, chash: str) -> str:
    fm = [
        "---",
        f"rule_set_id: {rid}",
        f"title: {json.dumps(page['title'], ensure_ascii=False)}",
        f"source_url: {page['url']}",
        f"platforms: {json.dumps(page['platforms'], ensure_ascii=False)}",
        f"category: {category_of(page['path'])}",
        f"hig_fetched: {fetched}",
        f"content_hash: {chash}",
        "---",
        "",
        f"# {page['title']}",
        "",
    ]
    body = ["\n".join(fm)]
    if page["abstract"]:
        body.append(page["abstract"] + "\n")

    rule_counter = 0
    for sec in page["sections"]:
        heading = sec["heading"]
        if heading and heading.lower() != "overview":
            body.append(f"## {heading}\n")
        for para in sec["paragraphs"]:
            body.append(para + "\n")
        for rule in sec["rules"]:
            rule_counter += 1
            sub_id = f"{rid}-{rule_counter:03d}"
            line = f"- **[{sub_id}]** **{rule['guideline']}**"
            if rule["explanation"]:
                line += f" {rule['explanation']}"
            body.append(line)
        if sec["rules"]:
            body.append("")

    if rule_counter == 0:
        body.append(
            "_This page is a hub/overview; see the linked component pages for "
            "checkable guidelines._\n"
        )
    return "\n".join(body).rstrip() + "\n"


def crawl(limit: int | None = None) -> dict:
    """BFS the HIG reference graph. Returns {path: page_dict}."""
    pages: dict = {}
    seen = set()
    queue = deque([""])  # "" == HIG root
    seen.add("")
    fetched_count = 0

    while queue:
        path = queue.popleft()
        data = hig.fetch_page_json(path)
        if data is None:
            print(f"  ! fetch failed: {hig.web_url(path)}", file=sys.stderr)
            continue
        page = hig.extract_page(data, path)
        pages[path] = page
        fetched_count += 1
        print(f"  [{fetched_count}] {page['title']}  ({path or 'root'})")

        for child in page["child_paths"]:
            if child not in seen:
                seen.add(child)
                queue.append(child)

        if limit and fetched_count >= limit:
            print(f"  (stopping early at limit={limit})")
            break
        time.sleep(CRAWL_DELAY_SECONDS)

    return pages


def load_manifest() -> dict:
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {}


def parse_frontmatter(text: str) -> dict:
    """Parse the simple `---` frontmatter block written by render_markdown."""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    fm = {}
    for line in text[3:end].strip().splitlines():
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key, val = key.strip(), val.strip()
        if val.startswith(("[", "\"")):
            try:
                val = json.loads(val)
            except Exception:
                pass
        fm[key] = val
    return fm


def reindex_from_files() -> int:
    """Rebuild manifest.json + index.json + VERSION from existing rule files,
    with no network access. Useful after a partial crawl or to repair state."""
    files = sorted(PAGES_DIR.glob("*.md"))
    if not files:
        print(f"No rule files in {PAGES_DIR}. Run a full build first.", file=sys.stderr)
        return 1
    manifest_pages, index = {}, {}
    latest = "1970-01-01"
    for f in files:
        fm = parse_frontmatter(f.read_text(encoding="utf-8"))
        path = "" if f.stem == "root" else f.stem.replace("__", "/")
        rel_file = f"pages/{f.name}"
        manifest_pages[path] = {"rule_set_id": fm.get("rule_set_id", rule_set_id(path)),
                                "title": fm.get("title", path),
                                "content_hash": fm.get("content_hash", ""),
                                "file": rel_file}
        index[fm.get("rule_set_id", rule_set_id(path))] = {
            "title": fm.get("title", path), "url": fm.get("source_url", ""),
            "platforms": fm.get("platforms", ["all"]), "file": rel_file,
            "category": fm.get("category", category_of(path)), "path": path}
        latest = max(latest, str(fm.get("hig_fetched", "")) or latest)
    manifest = {"corpus_version": latest, "built": latest, "source": hig.WEB_BASE,
                "page_count": len(files), "pages": manifest_pages}
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    VERSION_FILE.write_text(latest + "\n", encoding="utf-8")
    print(f"Reindexed {len(files)} pages -> manifest.json / index.json (version {latest})")
    return 0


def bump_version() -> str:
    today = _dt.date.today().isoformat()
    return today


def main() -> int:
    ap = argparse.ArgumentParser(description="Build/upgrade the offline HIG rules corpus.")
    ap.add_argument("--upgrade", action="store_true", help="diff against existing manifest")
    ap.add_argument("--reindex", action="store_true",
                    help="rebuild manifest/index from existing rule files (no network)")
    ap.add_argument("--limit", type=int, default=None,
                    help="cap number of pages (smoke test only; does NOT update manifest/index)")
    args = ap.parse_args()

    if args.reindex:
        return reindex_from_files()

    if args.limit and args.upgrade:
        print("ERROR: --limit cannot be combined with --upgrade (a partial crawl would "
              "corrupt the manifest diff). Run a full --upgrade.", file=sys.stderr)
        return 2

    prev = load_manifest() if args.upgrade else {}
    prev_pages = prev.get("pages", {}) if isinstance(prev, dict) else {}

    print("Crawling Apple Human Interface Guidelines ...")
    pages = crawl(limit=args.limit)
    if not pages:
        print("No pages fetched (network issue?). Aborting.", file=sys.stderr)
        return 1

    PAGES_DIR.mkdir(parents=True, exist_ok=True)
    fetched = _dt.date.today().isoformat()

    manifest_pages = {}
    index = {}
    added, changed, unchanged = [], [], []

    for path, page in sorted(pages.items()):
        rid = rule_set_id(path)
        chash = content_hash(page)
        slug = (path.replace("/", "__") or "root")
        rel_file = f"pages/{slug}.md"
        (PAGES_DIR / f"{slug}.md").write_text(
            render_markdown(page, rid, fetched, chash), encoding="utf-8"
        )

        manifest_pages[path] = {"rule_set_id": rid, "title": page["title"],
                                "content_hash": chash, "file": rel_file}
        index[rid] = {"title": page["title"], "url": page["url"],
                      "platforms": page["platforms"], "file": rel_file,
                      "category": category_of(path), "path": path}

        old = prev_pages.get(path)
        if old is None:
            added.append(path)
        elif old.get("content_hash") != chash:
            changed.append(path)
        else:
            unchanged.append(path)

    removed = [p for p in prev_pages if p not in pages] if args.upgrade else []
    version = bump_version()

    manifest = {
        "corpus_version": version,
        "built": fetched,
        "source": hig.WEB_BASE,
        "page_count": len(pages),
        "pages": manifest_pages,
    }
    if args.limit:
        # Smoke-test mode: rule files are written for inspection, but the
        # canonical manifest/index/VERSION are left untouched so a partial
        # crawl cannot corrupt the real corpus state.
        print("\n=== Smoke test (--limit) ===")
        print(f"pages written  : {len(pages)} -> {PAGES_DIR}")
        print("manifest.json / index.json / VERSION left unchanged (partial crawl).")
        return 0

    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    VERSION_FILE.write_text(version + "\n", encoding="utf-8")

    print("\n=== Build summary ===")
    print(f"corpus_version : {version}")
    print(f"pages written  : {len(pages)} -> {PAGES_DIR}")
    if args.upgrade:
        print(f"added   : {len(added)}")
        for p in added:
            print(f"   + {p or 'root'}")
        print(f"changed : {len(changed)}")
        for p in changed:
            print(f"   ~ {p or 'root'}")
        print(f"removed : {len(removed)}")
        for p in removed:
            print(f"   - {p or 'root'}")
        if not (added or changed or removed):
            print("No differences vs previous manifest.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
