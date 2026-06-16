# rules/ — generated HIG baseline (not committed)

This folder holds the offline rule corpus, **built locally**. It isn't shipped in
the repo: the text is derived from Apple's Human Interface Guidelines
(© Apple Inc.) and isn't redistributed here.

Build it once from the skill directory (needs network, ~15–20 min):

    python3 scripts/build_rules.py

That writes `pages/<slug>.md`, `index.json`, `manifest.json`, and `../VERSION`.
After that, reviews run fully offline. Update later with:

    python3 scripts/build_rules.py --upgrade
