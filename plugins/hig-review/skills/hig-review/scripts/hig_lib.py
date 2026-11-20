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

# Apple publishes official translations of the HIG. Each language lives under a
# path segment, e.g. zh-CN:
#   data: https://developer.apple.com/tutorials/data/cn/design/human-interface-guidelines/{path}.json
#   web : https://developer.apple.com/cn/design/human-interface-guidelines/{path}
# English is the canonical source (stable ids, change-log dates); translations
# are used for official localized titles/links and for quoting in reports.
LANG_SEGMENTS = {"en": "", "zh-CN": "cn", "ja-JP": "jp", "ko-KR": "kr"}

# Bump when extract_page() output changes shape, so --upgrade can tell a
# parser-induced diff from a real HIG content change.
PARSER_VERSION = 2

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
    # Drop "#Anchor" fragments and "?query" — references often point at a
    # section of a page (e.g. "buttons#Image-buttons"); those are not pages.
    p = p.split("#", 1)[0].split("?", 1)[0]
    for marker in ("/tutorials/data/design/human-interface-guidelines", WEB_PREFIX):
        if marker in p:
            p = p.split(marker, 1)[1]
            break
    p = p.strip("/")
    if p.endswith(".json"):
        p = p[: -len(".json")]
    return p


def _lang_segment(lang: str) -> str:
    if lang not in LANG_SEGMENTS:
        raise ValueError(f"unsupported HIG language {lang!r}; choose from {sorted(LANG_SEGMENTS)}")
    return LANG_SEGMENTS[lang]


def data_url(path: str, lang: str = "en") -> str:
    path = normalize_path(path)
    seg = _lang_segment(lang)
    base = DATA_BASE.replace("/tutorials/data/", f"/tutorials/data/{seg}/") if seg else DATA_BASE
    return f"{base}.json" if not path else f"{base}/{path}.json"


def web_url(path: str, lang: str = "en") -> str:
    path = normalize_path(path)
    seg = _lang_segment(lang)
    base = WEB_BASE.replace("developer.apple.com/", f"developer.apple.com/{seg}/") if seg else WEB_BASE
    return base if not path else f"{base}/{path}"


def fetch_page_json(path: str, timeout: int = 15, retries: int = 2,
                    lang: str = "en") -> Optional[Dict]:
    """Fetch and decode a HIG page's JSON. Returns None on failure."""
    url = data_url(path, lang)
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
        if tail == "iphone-duo":
            # iPhone Duo is an iPhone form factor (iOS); its page layers on
            # top of Designing for iOS rather than defining a new platform.
            return ["iOS"]
    if slug == "carplay":
        return ["CarPlay"]
    return ["all"]


_MONTHS = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July", "August",
     "September", "October", "November", "December"], 1)}


def latest_change(page: Dict) -> Optional[Dict]:
    """Return {"date": "YYYY-MM-DD", "change": "..."} for the newest entry of an
    (English) page's "Change log" table, or None if the page has no log."""
    best = None
    for sec in page.get("sections", []):
        if sec.get("heading", "").strip().lower() != "change log":
            continue
        for para in sec.get("paragraphs", []):
            for line in para.splitlines():
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if len(cells) < 2:
                    continue
                parts = cells[0].replace(",", "").split()
                if len(parts) != 3 or parts[0] not in _MONTHS:
                    continue
                try:
                    date = f"{int(parts[2]):04d}-{_MONTHS[parts[0]]:02d}-{int(parts[1]):02d}"
                except ValueError:
                    continue
                if best is None or date > best["date"]:
                    best = {"date": date, "change": cells[1]}
    return best


def extract_page(data: Dict, path: str, lang: str = "en") -> Dict:
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
    state = {"current": {"heading": "Overview", "level": 1, "paragraphs": [], "rules": []}}
    all_text_parts: List[str] = [abstract]

    def start_section(heading: str, level: int) -> None:
        cur = state["current"]
        if cur["paragraphs"] or cur["rules"]:
            sections.append(cur)
        state["current"] = {"heading": heading, "level": level, "paragraphs": [], "rules": []}

    def add_para(txt: str) -> None:
        if txt:
            state["current"]["paragraphs"].append(txt)
            all_text_parts.append(txt)

    def cell_text(cell: List[Dict]) -> str:
        parts = [inline_text(b.get("inlineContent", []), references) for b in cell or []]
        return " ".join(x for x in parts if x).replace("|", "/")

    def walk(nodes: List[Dict], prefix: str = "") -> None:
        """Walk DocC block content recursively. `prefix` tags text that lives
        inside a platform/variant tab (e.g. "[iOS] ...") so it isn't lost or
        misattributed when flattened."""
        for node in nodes or []:
            ntype = node.get("type")
            if ntype == "heading":
                start_section(node.get("text", ""), node.get("level", 2))
            elif ntype == "paragraph":
                if not node.get("inlineContent"):
                    continue
                if all(n.get("type") == "image" for n in node["inlineContent"]):
                    continue
                lead = _lead_strong(node, references)
                full = inline_text(node.get("inlineContent", []), references)
                if lead:
                    all_text_parts.append(full)
                    explanation = full[len(lead):].strip() if full.startswith(lead) else full
                    state["current"]["rules"].append(
                        {"guideline": prefix + lead, "explanation": explanation})
                elif full:
                    add_para(prefix + full)
            elif ntype in ("unorderedList", "orderedList"):
                for item in node.get("items", []):
                    walk(item.get("content", []), prefix)
            elif ntype == "aside":
                name = node.get("name") or node.get("style", "Note").title()
                for sub in node.get("content", []):
                    if sub.get("type") == "paragraph":
                        txt = inline_text(sub.get("inlineContent", []), references)
                        if txt:
                            add_para(f"{prefix}[{name}] {txt}")
                    else:
                        walk([sub], prefix)
            elif ntype == "table":
                # Tables carry hard numbers (sizes, spacing, type ramps) —
                # render them as Markdown table lines.
                rows = node.get("rows", [])
                if not rows:
                    continue
                lines = ["| " + " | ".join(cell_text(c) for c in r) + " |" for r in rows]
                if node.get("header") in ("row", "both") and len(lines) > 1:
                    lines.insert(1, "|" + "---|" * len(rows[0]))
                if prefix:
                    lines.insert(0, prefix.strip())
                add_para("\n".join(lines))
            elif ntype == "tabNavigator":
                # Platform / variant tabs (e.g. iOS | macOS | visionOS).
                for tab in node.get("tabs", []):
                    title = tab.get("title", "")
                    walk(tab.get("content", []), f"{prefix}[{title}] " if title else prefix)
            elif ntype == "row":
                for col in node.get("columns", []):
                    walk(col.get("content", []), prefix)
            elif ntype == "termList":
                for item in node.get("items", []):
                    term = inline_text(item.get("term", {}).get("inlineContent", []), references)
                    for sub in item.get("definition", {}).get("content", []):
                        txt = inline_text(sub.get("inlineContent", []), references)
                        if txt:
                            add_para(f"{prefix}{term}: {txt}" if term else prefix + txt)
            elif ntype == "small":
                add_para(prefix + inline_text(node.get("inlineContent", []), references))
            # links / image / video / thematicBreak carry no checkable text.

    for sec in data.get("primaryContentSections", []):
        if sec.get("kind") == "content":
            walk(sec.get("content", []))
    cur = state["current"]
    if cur["paragraphs"] or cur["rules"]:
        sections.append(cur)

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
        "url": web_url(path, lang),
        "title": title,
        "role": metadata.get("role", ""),
        "abstract": abstract,
        "platforms": platforms,
        "sections": sections,
        "child_paths": sorted(set(child_paths)),
    }
