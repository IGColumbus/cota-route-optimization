#!/usr/bin/env python3
"""Audit numbers in public-facing documents by scientific importance.

Every numeric token in the audited sections is put in exactly one class:

* ``checked``      part of a claim string that ``scripts/verify_report_claims.py``
                   checks against its artifact, appearing verbatim in this document;
* ``identifier``   a date, year, commit hash, section/figure/table/experiment/
                   level/rule label, or a count inside such a label;
* ``classified``   listed in ``docs/report/NUMBER_CLASSIFICATION.yaml`` with a
                   class (configuration constant, provenance/metadata,
                   bibliographic, descriptive/non-load-bearing, or scientific
                   with the artifact that backs it) and a reason;
* ``unclassified`` none of the above.

The release gate (``--check``) fails if any ``unclassified`` token is left in a
priority section. Priority sections are those where a number can change a
reader's interpretation:

* the abstract and highlights;
* the README's headline, results table and limitations;
* the report's summary table, limitations table, retraction table and
  conclusion;
* the two briefs.

Lower-priority sections are reported but do not fail the gate.

    python scripts/audit_public_numbers.py            # table of counts per section
    python scripts/audit_public_numbers.py --list     # also list unclassified tokens
    python scripts/audit_public_numbers.py --check    # release gate
"""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CLASSES = ROOT / "docs" / "report" / "NUMBER_CLASSIFICATION.yaml"
REPORT = "docs/report/TECHNICAL_REPORT.md"

# (document, start regex, end regex or None, label, priority)
SECTIONS = [
    (REPORT, r"^## Abstract", r"^\*\*Keywords", "report: abstract + highlights", True),
    (REPORT, r"^\*\*Summary of findings\*\*", r"^> Holding modeled", "report §1 summary table", True),
    (REPORT, r"^### 8\.1 Limitations table", r"^## 9\.", "report §8.1 limitations table", True),
    (REPORT, r"^## 9\. Retractions", r"^## 10\.", "report §9 retractions", True),
    (REPORT, r"^## 11\. Conclusion", r"^## Data and code availability", "report §11 conclusion", True),
    ("README.md", r"^## Bottom line", r"^## Quick start", "README headline, results, limitations", True),
    ("docs/PUBLIC_BRIEF.md", r"^## What was studied", None, "public brief", True),
    ("docs/PLANNING_BRIEF.md", r"^## 1\. The question", None, "planning brief", True),
    (REPORT, r"^## 5\. Results", r"^## 6\. Robustness", "report §5 results", False),
    (REPORT, r"^## 6\. Robustness", r"^## 7\. ", "report §6 robustness", False),
    ("docs/FINDINGS.md", r"^## Results by experiment", None, "FINDINGS", False),
]

NUM = re.compile(r"(?<![A-Za-z0-9_./#\-])[~+−\-]?\d[\d,]*(?:\.\d+)?%?")
LABEL_BEFORE = re.compile(
    r"(§\s?|Figure\s|Fig\.\s|Table\s|Exp\s|Experiment\s|Experiments\s|Stage\s|gate\s|Gate\s|"
    r"amendment\s|Amendment\s|Appendix\s|rule\s|R|E|D|C|F|G|A|B|N|S|J|H|Class\s|level\s|"
    r"seed\s|round\s|step\s|Step\s|phase\s|Phase\s|v|top-|#|Δ|errata\s|E[0-9]+–|ROUND|Round\s)$")


def load_claims():
    spec = importlib.util.spec_from_file_location("vrc", ROOT / "scripts" / "verify_report_claims.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.CLAIMS


def section_text(doc: str, start: str, end: str | None) -> str:
    lines = (ROOT / doc).read_text().splitlines()
    i = next(k for k, l in enumerate(lines) if re.search(start, l))
    j = len(lines)
    if end:
        j = next((k for k in range(i + 1, len(lines)) if re.search(end, lines[k])), len(lines))
    return "\n".join(lines[i:j])


def strip_noise(text: str) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"`[^`]*`", " ", text)                  # code, paths, hashes, keys
    text = re.sub(r"\]\([^)]*\)", "]", text)               # link targets
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    return text


def norm(tok: str) -> str:
    return tok.lstrip("~+−-").rstrip("%")


def classify(doc: str, text: str, claims, classes: dict) -> dict:
    # a claim's value check does not depend on the document, so any verified
    # claim string that appears verbatim in this document covers its numbers
    raw = (ROOT / doc).read_text()
    claimed = {norm(t) for c in claims if c[0] in raw for t in NUM.findall(c[0])}
    allow = {str(k): v for k, v in (classes.get(doc) or {}).items()}
    out = {"checked": [], "identifier": [], "classified": [], "unclassified": []}
    for m in NUM.finditer(text):
        tok = m.group(0)
        before = text[max(0, m.start() - 12):m.start()]
        after = text[m.end():m.end() + 1]
        n = norm(tok)
        line_start = text.rfind("\n", 0, m.start()) + 1
        prefix = text[line_start:m.start()]
        after2 = text[m.end():m.end() + 2]
        if n and n in claimed:
            out["checked"].append(tok)
        elif (re.fullmatch(r"(19|20)\d\d", n) or re.match(r"\d{4}-\d{2}", text[m.start():m.start() + 7])
              or LABEL_BEFORE.search(before)
              or re.search(r"λ\s?[=≥≤·]\s?$|λ ∈ \{[\d, ]*$|route\s$|\(\d+, $", before)      # λ values, route ids
              or re.fullmatch(r"[#\s]*|\|\s*|\s*", prefix) and re.match(r"[.\s]", after2)  # headings, list/table numbering
              or re.match(r"[A-Za-z]", after) or before.endswith("/ ")):                     # 2B, 4N, "4 / 4N"
            out["identifier"].append(tok)
        elif tok in allow or n in allow:
            out["classified"].append(tok)
            cls = (allow.get(tok) or allow.get(n))["class"]
            out.setdefault("_classes", {}).setdefault(cls, []).append(tok)
        else:
            out["unclassified"].append(tok)
            out.setdefault("_ctx", []).append((tok, text[max(0, m.start() - 50):m.end() + 25]))
    return out


def main() -> int:
    claims = load_claims()
    classes = yaml.safe_load(CLASSES.read_text()) if CLASSES.exists() else {}
    bad = 0
    print(f"{'section':42s} {'checked':>8s} {'ident':>6s} {'class.':>7s} {'traced':>7s} {'unclass.':>9s}")
    tot = {"checked": 0, "traced": 0}
    for doc, s, e, label, prio in SECTIONS:
        r = classify(doc, strip_noise(section_text(doc, s, e)), claims, classes)
        u = r["unclassified"]
        flag = "FAIL" if (prio and u) else ("    " if not u else "info")
        tr = len(r.get("_classes", {}).get("traced", []))
        if prio:
            tot["checked"] += len(r["checked"])
            tot["traced"] += tr
        print(f"{flag} {label:37s} {len(r['checked']):8d} {len(r['identifier']):6d} "
              f"{len(r['classified']):7d} {tr:7d} {len(u):9d}")
        if ("--list" in sys.argv) and u:
            print("      unclassified: " + ", ".join(sorted(set(u))))
        if ("--context" in sys.argv) and u and prio:
            for tok, ctx in r["_ctx"]:
                print(f"      {tok!r}: …{ctx!r}")
        bad += bool(prio and u)
    print(f"priority sections: {tot['checked']} scientific numbers machine-checked, "
          f"{tot['traced']} traced to a named source but not machine-checked")
    if "--check" in sys.argv:
        print(("ok  " if not bad else "FAIL") + " every decision-relevant number in priority sections "
              "is machine-checked or explicitly classified")
        return 1 if bad else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
