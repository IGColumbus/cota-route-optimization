#!/usr/bin/env python3
"""Reconstruct the condensed-to-original commit map and check public reachability.

`docs/research-record/exp3/HISTORY_NOTE.md` cites `EXP3_HISTORY_MAP.json`,
which was never committed. This script rebuilds the map additively from git
itself, without touching any commit:

* every commit on the condensed line (`exp3-clean` tip `63249104`, i.e. on
  `master`) that is not on the archival branch `exp3` is matched to the
  original commit(s) with the **same tree object** on `exp3` (the collapse
  reused original trees via `git commit-tree`, so tree identity is exact);
* every "Original commits A..B" and "cherry picked from commit X" reference
  in those commit messages is resolved;
* each referenced or matched original is classified as `public` (reachable
  from `master`, `exp3` or a public tag), `backup_only` (reachable only from
  the unpublished branch `backup-exp3-preclean`), or `unresolved`.

It then scans tracked Markdown for cited commit hashes and reports any that
are not publicly reachable.

    python scripts/reconstruct_history_map.py            # write the map
    python scripts/reconstruct_history_map.py --check    # exit 1 if a doc cites a non-public commit
                                                        # without saying so

Needs the full history: `master`, the archival branch `exp3` and the tags.
`backup-exp3-preclean` is used if present; without it, backup-only commits
are reported as `unresolved`.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "research-record" / "exp3" / "EXP3_HISTORY_MAP.reconstructed.json"
CONDENSED_TIP = "c875fa66"      # exp3-clean tip at the condensation (HISTORY_NOTE.md); ancestor of master
ARCHIVE = "e162d24b"            # branch exp3
BASE = "b014c26c"               # common base of exp3 and exp3-clean
BACKUP = "backup-exp3-preclean"
PUBLIC_TAGS = ["research-final", "exp3-final-v1", "exp3-frozen-v1", "gen1-frozen-v1",
               "pre-exp3-v1", "pre-exp3-v2"]
#: documents that are frozen or historical: their citations are reported but
#: do not fail --check (they are explained by docs/RELEASE_PROVENANCE.md)
HISTORICAL_PREFIXES = ("docs/research-record/", "experiments/", "docs/report/reviews/",
                       "outputs/", "docs/process/OPERATIONS.md",
                       # states explicitly which commits are unpublished, and why
                       "docs/RELEASE_PROVENANCE.md")


def git(*a: str, check: bool = True) -> str:
    r = subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True)
    if check and r.returncode:
        raise RuntimeError(r.stderr.strip())
    return r.stdout.strip()


def resolve(h: str) -> str | None:
    out = git("rev-parse", "-q", "--verify", f"{h}^{{commit}}", check=False)
    return out or None


def ancestor(a: str, b: str) -> bool:
    return subprocess.run(["git", "merge-base", "--is-ancestor", a, b], cwd=ROOT).returncode == 0


def have(ref: str) -> bool:
    return resolve(ref) is not None


def classify(sha: str | None, public_tips: list[str], backup: bool) -> str:
    if sha is None:
        return "unresolved"
    if any(ancestor(sha, t) for t in public_tips):
        return "public"
    if backup and ancestor(sha, BACKUP):
        return "backup_only"
    return "unresolved"


def build() -> dict:
    backup = have(BACKUP)
    public_tips = ["HEAD", ARCHIVE] + [t for t in PUBLIC_TAGS if have(t)]
    by_tree: dict[str, list[str]] = {}
    for line in git("rev-list", "--format=%T", f"{BASE}..{ARCHIVE}").splitlines():
        if line.startswith("commit "):
            cur = line.split()[1]
        else:
            by_tree.setdefault(line, []).append(cur)
    rows = []
    condensed = git("rev-list", "--reverse", CONDENSED_TIP, f"^{ARCHIVE}", f"^{BASE}").split()
    for c in condensed:
        tree = git("rev-parse", f"{c}^{{tree}}")
        msg = git("log", "-1", "--format=%B", c)
        refs = []
        m = re.search(r"Original commits ([0-9a-f]{7,40})\.\.([0-9a-f]{7,40})", msg)
        if m:
            refs += [("original_first", m.group(1)), ("original_last", m.group(2))]
        for x in re.findall(r"cherry picked from commit ([0-9a-f]{7,40})", msg):
            refs.append(("cherry_picked_from", x))
        resolved = []
        for kind, h in refs:
            sha = resolve(h)
            resolved.append({"kind": kind, "cited": h, "sha": sha,
                             "status": classify(sha, public_tips, backup)})
        same_tree = by_tree.get(tree, [])
        rows.append({"condensed": c, "subject": msg.splitlines()[0][:100],
                     "tree": tree,
                     "same_tree_on_exp3": same_tree[:3],
                     "cited_originals": resolved})
    # every original-commit reference in any commit message on master's history
    refs_all = []
    for c in git("rev-list", "master").split():
        msg = git("log", "-1", "--format=%B", c)
        for kind, h in ([("original_range", x) for pair in re.findall(
                r"Original commits ([0-9a-f]{7,40})\.\.([0-9a-f]{7,40})", msg) for x in pair]
                + [("cherry_picked_from", x) for x in re.findall(
                    r"cherry picked from commit ([0-9a-f]{7,40})", msg)]):
            sha = resolve(h)
            refs_all.append({"in_commit": c[:12], "kind": kind, "cited": h, "sha": sha,
                             "status": classify(sha, public_tips, backup)})
    return {"what": "Reconstructed condensed-to-original commit map for the Experiment 3 "
                    "history (HISTORY_NOTE.md cites EXP3_HISTORY_MAP.json, which was never "
                    "committed). Generated by scripts/reconstruct_history_map.py.",
            "condensed_tip": CONDENSED_TIP, "archive_branch_tip": ARCHIVE, "base": BASE,
            "backup_branch_available": backup,
            "n_condensed": len(rows),
            "n_matched_by_tree": sum(1 for r in rows if r["same_tree_on_exp3"]),
            "cited_original_status": _count(r2["status"] for r in rows for r2 in r["cited_originals"]),
            "rows": rows,
            "message_references_on_master": refs_all,
            "message_reference_status": _count(r["status"] for r in refs_all)}


def _count(it) -> dict:
    d: dict[str, int] = {}
    for x in it:
        d[x] = d.get(x, 0) + 1
    return d


HEX = re.compile(r"`([0-9a-f]{7,12})`")


def doc_citations() -> list[dict]:
    backup = have(BACKUP)
    public_tips = ["HEAD", ARCHIVE] + [t for t in PUBLIC_TAGS if have(t)]
    seen: dict[str, str] = {}
    out = []
    for f in git("ls-files", "*.md").splitlines():
        text = (ROOT / f).read_text(errors="replace")
        for h in set(HEX.findall(text)):
            if h not in seen:
                sha = resolve(h)
                seen[h] = classify(sha, public_tips, backup) if sha else "not_a_commit"
            if seen[h] in ("backup_only", "unresolved"):
                out.append({"file": f, "cited": h, "status": seen[h],
                            "historical_document": f.startswith(HISTORICAL_PREFIXES)})
    return out


def main() -> int:
    cites = doc_citations()
    live = [c for c in cites if not c["historical_document"]]
    if "--check" in sys.argv:
        for c in live:
            print(f"FAIL {c['file']}: cites {c['cited']} ({c['status']})")
        print(("ok  " if not live else "FAIL") + f" commit citations in live documents "
              f"({len(cites)} non-public citations in historical documents, explained in "
              "docs/RELEASE_PROVENANCE.md)")
        return 1 if live else 0
    m = build()
    m["doc_citations_not_public"] = cites
    OUT.write_text(json.dumps(m, indent=1) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}: {m['n_condensed']} condensed commits, "
          f"{m['n_matched_by_tree']} matched by tree; cited originals {m['cited_original_status']}; "
          f"all master message references {m['message_reference_status']}; "
          f"{len(cites)} doc citations not public ({len(live)} in live documents)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
