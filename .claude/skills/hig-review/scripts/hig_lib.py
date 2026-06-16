"""
HIG shared library
==================

Fetches and parses Apple Human Interface Guidelines content from the DocC JSON
endpoints, e.g.:

    https://developer.apple.com/tutorials/data/design/human-interface-guidelines/{path}.json

The public HIG pages are rendered client-side from these JSON documents, so they
are the reliable, structured source for both offline rule generation
(build_rules.py) and live online review (hig_fetch.py).

This module intentionally depends only on the Python standard library so the
skill stays self-contained (no pip install required).
"""

from __future__ import annotations

import json
import time
import urllib.request
import urllib.error
from typing import Dict, List, Optional

WEB_PREFIX = "/design/human-interface-guidelines"
DATA_BASE = "https://developer.apple.com/tutorials/data/design/human-interface-guidelines"
WEB_BASE = "https://developer.apple.com/design/human-interface-guidelines"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Accept": "application/json",
}

# Platform keywords used to infer which platforms a page/rule applies to when
# metadata.platforms is absent (it frequently is on component pages).
PLATFORM_KEYWORDS = {
    "iOS": "iOS",
    "iPadOS": "iPadOS",
    "macOS": "macOS",
    "watchOS": "watchOS",
    "tvOS": "tvOS",
    "visionOS": "visionOS",
    "CarPlay": "CarPlay",
}


def normalize_path(path_or_url: str) -> str:
    """Reduce a HIG path or URL to its canonical slug path.

    Accepts: "buttons", "/design/human-interface-guidelines/buttons",
    a full developer.apple.com URL, or "" / "/" for the root page.
    """
    p = (path_or_url or "").strip()
    for marker in ("/tutorials/data/design/human-interface-guidelines", WEB_PREFIX):
        if marker in p:
            p = p.split(marker, 1)[1]
            break
    p = p.strip("/")
    if p.endswith(".json"):
        p = p[: -len(".json")]
    return p


def data_url(path: str) -> str:
    path = normalize_path(path)
    return f"{DATA_BASE}.json" if not path else f"{DATA_BASE}/{path}.json"


def web_url(path: str) -> str:
    path = normalize_path(path)
    return WEB_BASE if not path else f"{WEB_BASE}/{path}"


def fetch_page_json(path: str, timeout: int = 15, retries: int = 2) -> Optional[Dict]:
    """Fetch and decode a HIG page's JSON. Returns None on failure."""
    url = data_url(path)
    last_err = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status == 200:
                    return json.loads(resp.read())
        except Exception as e:  # noqa: BLE001 - network errors are expected/handled
            last_err = e
            if attempt < retries:
                time.sleep(1.0 + attempt)
    if last_err:
        # Caller decides how to report; keep library quiet.
        pass
    return None


def inline_text(nodes: List[Dict], references: Optional[Dict] = None) -> str:
    """Recursively flatten DocC inlineContent into plain text."""
    references = references or {}
    out: List[str] = []
    for n in nodes or []:
        t = n.get("type")
        if t == "text":
            out.append(n.get("text", ""))
        elif t == "codeVoice":
            out.append(n.get("code", n.get("text", "")))
        elif t in ("strong", "emphasis", "newTerm", "superscript", "subscript"):
            out.append(inline_text(n.get("inlineContent", []), references))
        elif t == "reference":
            ref = references.get(n.get("identifier", ""), {})
            out.append(ref.get("title", "") or "")
        elif t == "link":
            out.append(n.get("title", ""))
        elif t == "inlineHead":
            out.append(inline_text(n.get("inlineContent", []), references))
        # images / unknown inline types contribute no text
    return "".join(out).strip()


def _lead_strong(node: Dict, references: Dict) -> Optional[str]:
    """If a paragraph begins with a <strong> imperative, return that lead text."""
    inline = node.get("inlineContent", [])
    if inline and inline[0].get("type") == "strong":
        return inline_text(inline[0].get("inlineContent", []), references)
    return None


def _platforms_for_page(path: str) -> List[str]:
    """Determine applicable platforms for a page.

    HIG component / foundation / pattern pages apply broadly; platform-specific
    nuance lives in inline notes within those pages (e.g. "in visionOS,
    60x60 pt"), which the reviewer reads directly. Only the "Designing for X"
    hub pages are inherently platform-exclusive. So we default to "all" and
    special-case the platform hubs — keyword scanning under-tags broadly
    applicable pages (e.g. Buttons) and would wrongly exclude them from a
    platform's review.
    """
    slug = path.lower()
    if slug.startswith("designing-for-"):
        tail = slug.replace("designing-for-", "")
        for key, label in PLATFORM_KEYWORDS.items():
            if tail == key.lower():
                return [label]
    if slug == "carplay":
        return ["CarPlay"]
    return ["all"]


def extract_page(data: Dict, path: str) -> Dict:
    """Parse a HIG page JSON into a normalized structure.

    Returns dict with: path, url, title, role, abstract, platforms,
    sections (list of {heading, level, paragraphs, rules}), child_paths.
    A "rule" is a Best-practices-style paragraph led by a <strong> imperative.
    """
    references = data.get("references", {})
    metadata = data.get("metadata", {})
    title = metadata.get("title", path or "Human Interface Guidelines")
    abstract = inline_text(data.get("abstract", []), references)

    sections: List[Dict] = []
    current = {"heading": "Overview", "level": 1, "paragraphs": [], "rules": []}
    all_text_parts: List[str] = [abstract]

    for sec in data.get("primaryContentSections", []):
        if sec.get("kind") != "content":
            continue
        for node in sec.get("content", []):
            ntype = node.get("type")
            if ntype == "heading":
                if current["paragraphs"] or current["rules"]:
                    sections.append(current)
                current = {
                    "heading": node.get("text", ""),
                    "level": node.get("level", 2),
                    "paragraphs": [],
                    "rules": [],
                }
            elif ntype == "paragraph":
                lead = _lead_strong(node, references)
                full = inline_text(node.get("inlineContent", []), references)
                all_text_parts.append(full)
                if lead:
                    explanation = full[len(lead):].strip() if full.startswith(lead) else full
                    current["rules"].append({"guideline": lead, "explanation": explanation})
                elif full:
                    current["paragraphs"].append(full)
            elif ntype in ("unorderedList", "orderedList"):
                for item in node.get("items", []):
                    for sub in item.get("content", []):
                        txt = inline_text(sub.get("inlineContent", []), references)
                        if txt:
                            current["paragraphs"].append(txt)
                            all_text_parts.append(txt)
            elif ntype == "aside":
                for sub in node.get("content", []):
                    txt = inline_text(sub.get("inlineContent", []), references)
                    if txt:
                        note = f"[{node.get('name', 'Note')}] {txt}"
                        current["paragraphs"].append(note)
                        all_text_parts.append(txt)
    if current["paragraphs"] or current["rules"]:
        sections.append(current)

    # Child pages for BFS crawling: any reference whose url is under the HIG tree.
    child_paths = []
    for ref in references.values():
        if not isinstance(ref, dict):
            continue
        url = ref.get("url", "")
        if url.startswith(WEB_PREFIX) and ref.get("type") == "topic":
            child_paths.append(normalize_path(url))

    platforms = metadata.get("platforms")
    if platforms:
        platforms = [p.get("name") if isinstance(p, dict) else p for p in platforms]
    else:
        platforms = _platforms_for_page(path)

    return {
        "path": path,
        "url": web_url(path),
        "title": title,
        "role": metadata.get("role", ""),
        "abstract": abstract,
        "platforms": platforms,
        "sections": sections,
        "child_paths": sorted(set(child_paths)),
    }
