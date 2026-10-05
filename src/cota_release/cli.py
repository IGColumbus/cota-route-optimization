"""`cota-opt` console entry point.

`cota-opt reproduce ...` is handled here; every other subcommand is passed to
the research CLI (`cota_opt.cli`) unchanged.
"""
from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "reproduce":
        ap = argparse.ArgumentParser(prog="cota-opt reproduce")
        ap.add_argument("experiment", choices=["exp1"])
        ap.add_argument("--smoke", action="store_true",
                        help="re-evaluate the current plan and the three certified "
                             "Exp 1 plans (minutes); no optimization")
        ap.add_argument("--seeds", default="20260825,20260826,20260827")
        ap.add_argument("--out", default=None, help="write the reproduction record here")
        a = ap.parse_args(argv[1:])
        from cota_release import reproduce
        return reproduce.exp1(smoke=a.smoke, seeds=[int(s) for s in a.seeds.split(",")],
                              out=a.out)
    if argv and argv[0] == "data":
        ap = argparse.ArgumentParser(prog="cota-opt data",
                                     description="stage the registered raw inputs under data/raw/")
        sub = ap.add_subparsers(dest="cmd", required=True)
        sub.add_parser("status", help="which required inputs are registered")
        p = sub.add_parser("register", help="register a file you downloaded yourself")
        p.add_argument("key")
        p.add_argument("file")
        p = sub.add_parser("fetch", help="download from the URL in config/sources.yaml")
        p.add_argument("key")
        a = ap.parse_args(argv[1:])
        from cota_release import data
        if a.cmd == "status":
            return data.status()
        if a.cmd == "register":
            return data.register(a.key, a.file)
        return data.fetch(a.key)
    from cota_opt.cli import main as research_main
    if not argv or argv[0] in ("-h", "--help"):
        print("cota-opt data status|register|fetch   stage the raw inputs (see docs/REPRODUCE.md §0)\n"
              "cota-opt reproduce exp1 [--smoke]   reproduce Experiment 1 (see docs/REPRODUCE.md)\n")
    return research_main(argv)


if __name__ == "__main__":
    sys.exit(main())
