#!/usr/bin/env python3
"""Write the model-status box into the briefs from config/model_status.yaml.

The box sits between `<!-- model-status:begin -->` and `<!-- model-status:end -->`
and is generated, never typed, so it cannot drift from the recorded status.

    python scripts/model_status_box.py           # update the briefs
    python scripts/model_status_box.py --check   # exit 1 if a box is stale or missing
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from cota_release.model_status import render_box  # noqa: E402

DOCS = ["docs/PUBLIC_BRIEF.md", "docs/PLANNING_BRIEF.md"]
BEGIN, END = "<!-- model-status:begin -->", "<!-- model-status:end -->"


def main() -> int:
    box = BEGIN + "\n" + render_box() + "\n" + END
    bad = 0
    for rel in DOCS:
        p = ROOT / rel
        text = p.read_text()
        if BEGIN not in text or END not in text:
            print(f"FAIL {rel}: no model-status markers")
            bad += 1
            continue
        new = text[:text.index(BEGIN)] + box + text[text.index(END) + len(END):]
        if "--check" in sys.argv:
            ok = new == text
            print(("ok  " if ok else "FAIL") + f" model-status box in {rel}")
            bad += not ok
        else:
            p.write_text(new)
            print(f"updated {rel}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
