"""Inventory every repository path that tracked files refer to.

Writes ``docs/research-record/PATH_REFERENCE_MAP.json``: for each tracked file
that is referred to by another tracked file, the list of referring files (with
line numbers) and the class of each referrer (doc, report, registry, script,
src, test, config, manifest, artifact).

Run before any restructure (P1-16) and again after, with ``--check`` to list
references in release-facing files that no longer resolve.

Usage:
    python scripts/build_path_reference_map.py            # write the map
    python scripts/build_path_reference_map.py --check    # broken-reference scan
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "research-record" / "PATH_REFERENCE_MAP.json"
TOKEN = re.compile(r"[A-Za-z0-9_./\-{}*]+\.(?:md|py|json|jsonl|csv|ya?ml|toml|log|txt|sh|svg|png|cff)\b")
TEXT_EXT = {".md", ".py", ".json", ".yaml", ".yml", ".toml", ".sh", ".txt", ".cfg", ".cff", ".ini"}
MAX_BYTES = 3_000_000

# files whose paths are history, not live references: never rewritten
FROZEN_PREFIXES = ("outputs/",)
FROZEN_DOCS = {
    "EXPERIMENT2_CLOSEOUT.md", "EXPERIMENT3_CLOSEOUT.md", "EXPERIMENT3_CLOSURE.md",
    "EXPERIMENT4_CLOSEOUT.md", "EXPERIMENT4_NORMALIZED_CLOSEOUT.md",
    "EXPERIMENT4_ORIGINAL_QUESTION_ADDENDUM.md", "EXPERIMENT5_CLOSEOUT.md",
    "EXPERIMENT6_CLOSEOUT.md", "EXPERIMENT7_CLOSEOUT.md", "DISCOVERIES.md",
}
RELEASE_FACING = ("README.md", "AGENTS.md", "CITATION.cff", "pyproject.toml",
                  "docs/report/", "docs/REPRODUCE.md", "docs/GLOSSARY.md",
                  "docs/RELEASE_PROVENANCE.md", "docs/REPORTING_CORRECTIONS.md",
                  "docs/ENGINEERING_RULES.md", "docs/FUTURE_EXPERIMENTS.md",
                  "docs/research-record/MOVES.md", "experiments/", ".github/")


def tracked() -> list[str]:
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True)
    return out.stdout.splitlines()


def klass(p: str) -> str:
    if p.startswith("outputs/") and "CANONICAL_RESULTS" in p:
        return "registry"
    if p.startswith("outputs/"):
        return "artifact"
    if p.startswith("docs/report/figures/") and p.endswith(".json"):
        return "manifest"
    if p.startswith("docs/report/"):
        return "report"
    if p.startswith("src/"):
        return "src"
    if p.startswith("tests/"):
        return "test"
    if p.startswith("scripts/") or p.startswith("experiments/") and p.endswith((".py", ".sh")):
        return "script"
    if p.startswith("config/"):
        return "config"
    return "doc"


def build(files: list[str]) -> dict:
    fileset = set(files)
    by_base: dict[str, list[str]] = defaultdict(list)
    for f in files:
        by_base[Path(f).name].append(f)
    refs: dict[str, list[dict]] = defaultdict(list)
    for src in files:
        p = ROOT / src
        if p.suffix not in TEXT_EXT or not p.is_file() or p.stat().st_size > MAX_BYTES:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for ln, line in enumerate(text.splitlines(), 1):
            for tok in set(TOKEN.findall(line)):
                tok = tok.strip("./") if tok.startswith("./") else tok
                targets = []
                if tok in fileset:
                    targets = [tok]
                elif "/" not in tok and tok in by_base and len(by_base[tok]) == 1:
                    targets = by_base[tok]
                for t in targets:
                    if t != src:
                        refs[t].append({"from": src, "line": ln, "class": klass(src)})
    return refs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    files = tracked()
    if a.check:
        fileset = set(files)
        bases = {Path(f).name for f in files}
        broken = []
        for src in files:
            if not src.startswith(RELEASE_FACING) or not (ROOT / src).is_file():
                continue
            if (ROOT / src).suffix not in TEXT_EXT:
                continue
            for ln, line in enumerate((ROOT / src).read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                for tok in set(TOKEN.findall(line)):
                    if any(c in tok for c in "{}*"):
                        continue
                    t = tok[2:] if tok.startswith("./") else tok
                    if t in fileset or ("/" not in t and t in bases):
                        continue
                    if "/" in t and (ROOT / t).exists():
                        continue  # untracked but present (e.g. generated)
                    if "/" in t and any(f.endswith("/" + t) for f in files):
                        continue  # relative reference that resolves under some dir
                    broken.append({"file": src, "line": ln, "ref": t})
        print(json.dumps({"broken": len(broken), "items": broken[:200]}, indent=1))
        return 1 if broken else 0
    refs = build(files)
    out = {
        "generated_by": "scripts/build_path_reference_map.py",
        "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                                 text=True).stdout.strip(),
        "n_tracked_files": len(files),
        "n_referenced_files": len(refs),
        "frozen_docs_never_rewritten": sorted(FROZEN_DOCS),
        "references": {k: v for k, v in sorted(refs.items())},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1) + "\n")
    print(f"{len(refs)} referenced files; written {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
