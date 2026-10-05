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
                        help="no optimization: rebuild the instance and re-evaluate the current "
                             "plan and the three certified plans (first run ~40 min "
                             "for the path-set build, then seconds from data/cache/)")
        ap.add_argument("--seeds", default="20260825,20260826,20260827",
                        help="comma-separated certified seeds to check (default: all three)")
        ap.add_argument("--out", default=None, help="write the reproduction record here")
        ap.add_argument("--state", default=None,
                        help="full run only: checkpoint file for restart-safe resume "
                             "(default: <out>.state.jsonl)")
        a = ap.parse_args(argv[1:])
        from cota_release import reproduce
        return reproduce.exp1(smoke=a.smoke, seeds=[int(s) for s in a.seeds.split(",")],
                              out=a.out, state=a.state)
    if argv and argv[0] == "run-script":
        # Run a research script with the container-path redirect applied
        # (docs/REPRODUCE.md §0): cota-opt run-script scripts/seed_check.py --common-lines same_route
        if len(argv) < 2:
            print("usage: cota-opt run-script <scripts/x.py> [args...]")
            return 2
        import runpy
        from cota_release.reproduce import redirect_container_paths
        redirect_container_paths()
        sys.argv = [argv[1], *argv[2:]]
        runpy.run_path(argv[1], run_name="__main__")
        return 0
    if argv and argv[0] == "validate-model":
        ap = argparse.ArgumentParser(
            prog="cota-opt validate-model",
            description="external validation on four independent dimensions (route volume, "
                        "stop pattern, transfer behavior, trip length); each reports passed, "
                        "failed or unavailable. Not the research CLI's `validate`, which checks "
                        "GTFS feed structure.")
        ap.add_argument("--config", default=None, help="default: config/validation.yaml")
        ap.add_argument("--modeled", default=None, help="JSON of modeled metrics per dimension")
        ap.add_argument("--from-study", action="store_true",
                        help="compute modeled route volumes from the study model "
                             "(needs the registered raw inputs)")
        ap.add_argument("--out", default=None, help="write the validation artifact here")
        a = ap.parse_args(argv[1:])
        from cota_release import validation
        return validation.run(config=a.config or validation.CONFIG, modeled_file=a.modeled,
                              from_study=a.from_study, out=a.out)
    if argv and argv[0] == "data":
        ap = argparse.ArgumentParser(prog="cota-opt data",
                                     description="stage the registered raw inputs under data/raw/")
        sub = ap.add_subparsers(dest="cmd", required=True)
        sub.add_parser("status", help="which required inputs are registered")
        p = sub.add_parser("register", help="register a file you downloaded yourself (copied; "
                                            "the original is left in place)")
        p.add_argument("key", help="source key, e.g. lodes_od_oh (see `cota-opt data status`)")
        p.add_argument("file", help="path to the downloaded file")
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
        print("Release commands (use these):\n"
              "  cota-opt data status|register|fetch   stage the five raw inputs (docs/REPRODUCE.md §0)\n"
              "  cota-opt reproduce exp1 [--smoke]     reproduce Experiment 1 (docs/REPRODUCE.md)\n"
              "  cota-opt validate-model               external validation, four dimensions\n"
              "                                        (docs/DATA_INTERFACES.md)\n\n"
              "Research commands (below). `validate` there checks GTFS feed structure only.\n"
              "`ingest-gtfs`, `download-gtfs` and `sources` are the\n"
              "older forms of `data register/fetch/status`; `sources` also lists optional sources\n"
              "(GTFS-Realtime, GIS, NTD) that no experiment needs as raw files.\n")
    return research_main(argv)


if __name__ == "__main__":
    sys.exit(main())
