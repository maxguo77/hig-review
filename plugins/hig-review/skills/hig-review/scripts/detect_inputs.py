#!/usr/bin/env python3
"""
Project input discovery & classification.
=========================================

Scans a project directory and produces a JSON inventory the review workflow
uses to decide *what* to review and *which* HIG rule sets are relevant:

  - code            : Swift / SwiftUI / UIKit / AppKit / Obj-C / web sources
  - design_images   : screenshots / mockups (png/jpg/pdf...) for visual review
  - design_sources  : .pen (Pencil MCP), .fig, .sketch
  - docs            : markdown / text / pdf specs (UX flows, requirements)
  - configs         : Info.plist, *.xcassets, storyboards/xibs, localization
  - component_hits  : UI symbols found in code, with file:line + candidate
                      HIG rule sets (resolve against rules/index.json)

Usage:
    python detect_inputs.py [PROJECT_DIR]      # default: current directory
    python detect_inputs.py PROJECT_DIR --pretty

The component map is a *best-guess* starting point; the skill does the real
reasoning and confirms candidate rule sets against the bundled index.
Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

IGNORE_DIRS = {".git", "node_modules", "build", "DerivedData", "Pods", ".claude",
               "Carthage", ".build", "dist", "out", "vendor", "__pycache__",
               ".next", ".venv", "venv"}

CODE_EXTS = {".swift", ".m", ".mm", ".h", ".js", ".jsx", ".ts", ".tsx",
             ".vue", ".html", ".htm", ".css", ".scss"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".heic", ".tiff", ".bmp"}
DESIGN_SOURCE_EXTS = {".pen", ".fig", ".sketch"}
DOC_EXTS = {".md", ".markdown", ".txt", ".rst", ".pdf", ".docx"}
CONFIG_EXTS = {".storyboard", ".xib", ".strings", ".xcstrings", ".plist"}

# UI symbol -> candidate HIG rule_set_ids (HIG-<SLUG>, see rules/index.json).
# Patterns are matched case-sensitively as word-ish tokens.
COMPONENT_MAP = [
    (r"\bButton\b|UIButton|NSButton|<button|role=[\"']button", ["HIG-BUTTONS"]),
    (r"TabView|UITabBar|TabItem|role=[\"']tab", ["HIG-TAB-BARS"]),
    (r"NavigationStack|NavigationView|UINavigationController|UINavigationBar",
     ["HIG-NAVIGATION-AND-SEARCH"]),
    (r"NavigationSplitView|NSSplitView|UISplitViewController", ["HIG-SPLIT-VIEWS"]),
    (r"\bsidebar\b|Sidebar|\.listStyle\(\.sidebar", ["HIG-SIDEBARS"]),
    (r"\.sheet\(|UIModalPresentationStyle|presentationDetents", ["HIG-SHEETS"]),
    (r"\bAlert\b|UIAlertController|\.alert\(", ["HIG-ALERTS"]),
    (r"\.popover\(|UIPopover", ["HIG-POPOVERS"]),
    (r"ActionSheet|\.confirmationDialog\(", ["HIG-ACTION-SHEETS"]),
    (r"Toolbar|NSToolbar|\.toolbar\b", ["HIG-TOOLBARS"]),
    (r"\bMenu\b|UIMenu|NSMenu|contextMenu", ["HIG-MENUS"]),
    (r"\bList\b|UITableView|NSTableView|UICollectionView", ["HIG-LISTS-AND-TABLES"]),
    (r"\bForm\b", ["HIG-ENTERING-DATA", "HIG-INPUTS"]),
    (r"TextField|UITextField|<input|NSTextField", ["HIG-TEXT-FIELDS"]),
    (r"SearchField|\.searchable\(|UISearchBar", ["HIG-SEARCH-FIELDS"]),
    (r"\bToggle\b|UISwitch|NSSwitch", ["HIG-TOGGLES"]),
    (r"\bPicker\b|UIPickerView|DatePicker|UIDatePicker", ["HIG-PICKERS"]),
    (r"\bSlider\b|UISlider|NSSlider", ["HIG-SLIDERS"]),
    (r"\bStepper\b|UIStepper", ["HIG-STEPPERS"]),
    (r"ProgressView|UIActivityIndicator|UIProgressView", ["HIG-PROGRESS-INDICATORS"]),
    (r"ColorPicker|NSColorWell", ["HIG-COLOR-WELLS"]),
    (r"Image\(systemName:|UIImage\(systemName:|SF\s?Symbol", ["HIG-SF-SYMBOLS"]),
    (r"\.font\(|UIFont|NSFont|font-size|fontWeight|Dynamic Type|dynamicType",
     ["HIG-TYPOGRAPHY"]),
    (r"\.foregroundColor\(|UIColor|NSColor|backgroundColor|color:\s*#", ["HIG-COLOR"]),
    (r"accessibilityLabel|accessibilityHint|aria-|VoiceOver|.accessibility",
     ["HIG-ACCESSIBILITY"]),
    (r"\.onTapGesture|UITapGestureRecognizer|hitTest|frame\(width:|min(Width|Height)",
     ["HIG-GESTURES"]),
    (r"LiquidGlass|\.glassEffect|Liquid Glass|materialEffect|\.ultraThinMaterial",
     ["HIG-MATERIALS"]),
    (r"@AppStorage|UserDefaults|onboarding|Onboarding", ["HIG-ONBOARDING"]),
    (r"requestAuthorization|AVCapture|CLLocationManager|requestWhenInUse",
     ["HIG-PRIVACY"]),
    (r"launchScreen|LaunchScreen|SplashScreen", ["HIG-LAUNCHING"]),
]


def classify_ext(name: str, ext: str) -> str | None:
    lower = name.lower()
    if lower == "info.plist" or ext == ".plist":
        return "configs"
    if ext in CONFIG_EXTS:
        return "configs"
    if ext in CODE_EXTS:
        return "code"
    if ext in IMAGE_EXTS:
        return "design_images"
    if ext in DESIGN_SOURCE_EXTS:
        return "design_sources"
    if ext in DOC_EXTS:
        return "docs"
    return None


def scan_component_hits(path: Path, rel: str) -> list[dict]:
    hits = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return hits
    lines = text.splitlines()
    for i, line in enumerate(lines, start=1):
        for pattern, rule_sets in COMPONENT_MAP:
            if re.search(pattern, line):
                hits.append({
                    "file": rel,
                    "line": i,
                    "match": line.strip()[:160],
                    "rule_sets": rule_sets,
                })
                break  # one hit per line is enough to flag it for review
    return hits


def main() -> int:
    ap = argparse.ArgumentParser(description="Classify project inputs for HIG review.")
    ap.add_argument("root", nargs="?", default=".", help="project directory")
    ap.add_argument("--pretty", action="store_true")
    ap.add_argument("--max-hits", type=int, default=800)
    args = ap.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"ERROR: path does not exist: {root}", file=sys.stderr)
        return 1

    buckets = {"code": [], "design_images": [], "design_sources": [],
               "docs": [], "configs": []}
    xcassets = []
    component_hits = []

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        # Treat *.xcassets as a single config artifact, don't descend.
        for d in list(dirnames):
            if d.endswith(".xcassets"):
                xcassets.append(os.path.relpath(os.path.join(dirpath, d), root))
                dirnames.remove(d)
        for fn in filenames:
            if fn.startswith("."):
                continue
            full = Path(dirpath) / fn
            rel = os.path.relpath(full, root)
            ext = full.suffix.lower()
            bucket = classify_ext(fn, ext)
            if bucket is None:
                continue
            buckets[bucket].append(rel)
            if bucket == "code" and len(component_hits) < args.max_hits:
                component_hits.extend(scan_component_hits(full, rel))

    if xcassets:
        buckets["configs"].extend(f"{x} (asset catalog)" for x in xcassets)

    inventory = {
        "root": str(root),
        "summary": {k: len(v) for k, v in buckets.items()},
        "component_hit_count": len(component_hits),
        **buckets,
        "component_hits": component_hits[: args.max_hits],
    }
    indent = 2 if args.pretty else None
    print(json.dumps(inventory, ensure_ascii=False, indent=indent))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
