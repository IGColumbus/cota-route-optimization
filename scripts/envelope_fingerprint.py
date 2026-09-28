#!/usr/bin/env python3
"""Exact (bit-lossless) resource-envelope fingerprint.  ADDITIVE — v1.

WHY THIS EXISTS
---------------
`envelope_digest` (`scripts/exp4n_freeze_envelope.py:100-105`) hashes
`round(peak[p], 9)`.  Two envelopes differing below the ninth decimal place
therefore hash the SAME.  That is not a hypothetical: during the EXP4N contract
freeze two hand-transcribed peak values were wrong in the last ULP (midday
...78 vs ...75, evening ...33 vs ...36) and the digest matched both times.
`docs/ENVELOPE_DIGEST_INSUFFICIENCY.md` is the audit note.  `--selftest`
replays that exact pair below.

`envelope_digest` is therefore NECESSARY BUT NOT SUFFICIENT for bit-exact
envelope identity.  This module supplies the sufficient one: the same INPUTS,
encoded losslessly instead of rounded.

SCOPE — read this before using it anywhere
------------------------------------------
This is ADDITIONAL, for experiments AFTER EXP4N, per Ian's instruction of
2026-09-25.  Three constraints on it are not negotiable:

  * It is NOT retrofitted into the EXP4N production contract, which is frozen
    as it stands.
  * It does NOT invalidate the EXP4N run.  That run's envelope identity was
    already established, before launch, by bit-exact assertions against two
    independent sources (the frozen artifact, and the `peak_caps` recorded by
    all 21 accepted calibration results).  A fingerprint computed here is a
    reference value, never a verdict on a completed run.
  * It does NOT replace `envelope_digest` in any artifact already written.

It also lives in `scripts/`, deliberately, NOT in `src/cota_opt`.  EXP4N's
records pin `src_cota_opt_content_digest = add5d0002d29aa49`, computed over
`src/cota_opt/**/*.py`; a module added there would move that digest and make
the completed run's own provenance assertions fail against its own tree.  A
future experiment that wants this in `src/` moves it at ITS preregistration,
where re-pinning the digest is legitimate.

WHAT IT GUARANTEES, AND WHAT IT DOES NOT
----------------------------------------
Guaranteed: two calls agree if and only if the encoded values are bit-identical
in IEEE-754, with identical keys, types, and structure.  Equal fingerprints
mean bit-equal inputs.

NOT guaranteed, and worth saying out loud because the rounded digest's failure
was exactly this kind of overreading: a matching fingerprint says the envelope
is the same NUMBER.  It says nothing about whether that number is the right
cap, was resolved against the right network, or was measured with an instrument
the contract permits.  `cap_provenance` answers those and this does not.

DELIBERATE ENCODING CHOICES
---------------------------
Each is a case where "obviously equal" and "bit-equal" diverge.  This function
reports bit-equality, so in every one of these it reports a DIFFERENCE, and the
caller decides whether the difference matters:

  * `-0.0` and `0.0` fingerprint DIFFERENTLY.  They are the same constraint and
    different bits.  A cap that acquired a sign is a provenance change worth
    seeing; the original complaint about `envelope_digest` was false agreement,
    so this errs the other way.
  * `197` (int) and `197.0` (float) fingerprint DIFFERENTLY, and are tagged by
    type.  `ResourceEnvelope` holds fleet per period as ints while the EXP4N
    peak envelope holds floats; a silent int/float swap is exactly the kind of
    substitution that looks equal in a log line.
  * `inf` encodes cleanly (it is a legal IEEE-754 pattern, and `OFF` is
    `math.inf` throughout this project, `frequency.py:121`).  Unlike JSON,
    which emits a non-standard bare `Infinity`, nothing here is lossy about it.
  * NaN is REFUSED, not encoded.  NaN != NaN, so any fingerprint over it would
    be claiming an identity relation that the value does not have.  An envelope
    containing NaN is not an envelope.

Encoding is type-tagged and length-prefixed, so no two distinct structures can
concatenate to the same byte string, and dict order cannot change the result
(keys are sorted by their own encoding, and every key is hashed with its
value).
"""
from __future__ import annotations
import hashlib, json, math, struct, sys
from pathlib import Path
from typing import Any

FINGERPRINT_VERSION = "exact-envelope-fp/v1"
PERIODS = ("early", "am_peak", "midday", "pm_peak", "evening", "owl")


class NotFingerprintable(ValueError):
    """Raised rather than encoding a value whose identity is not well defined."""


def _frame(tag: bytes, payload: bytes) -> bytes:
    assert len(tag) == 1
    return tag + struct.pack(">Q", len(payload)) + payload


def _enc(obj: Any, _depth: int = 0) -> bytes:
    if _depth > 32:
        raise NotFingerprintable("structure nested deeper than 32 levels")
    if obj is None:
        return _frame(b"n", b"")
    # bool before int: bool IS an int subclass, and True must not encode as 1.
    if isinstance(obj, bool):
        return _frame(b"b", b"\x01" if obj else b"\x00")
    if isinstance(obj, int):
        return _frame(b"i", str(obj).encode("ascii"))
    if isinstance(obj, float):
        if math.isnan(obj):
            raise NotFingerprintable(
                "NaN has no identity relation with itself; an envelope "
                "containing NaN is not a valid envelope")
        return _frame(b"f", struct.pack(">d", obj))
    if isinstance(obj, str):
        return _frame(b"s", obj.encode("utf-8"))
    if isinstance(obj, bytes):
        return _frame(b"y", obj)
    if isinstance(obj, (list, tuple)):
        return _frame(b"L", b"".join(_enc(v, _depth + 1) for v in obj))
    if isinstance(obj, dict):
        items = sorted(((_enc(k, _depth + 1), v) for k, v in obj.items()),
                       key=lambda kv: kv[0])
        seen = set()
        for ek, _ in items:
            if ek in seen:
                raise NotFingerprintable("two keys encode identically")
            seen.add(ek)
        return _frame(b"D", b"".join(ek + _enc(v, _depth + 1) for ek, v in items))
    raise NotFingerprintable(
        f"no lossless encoding declared for {type(obj).__name__}; add one "
        f"deliberately rather than falling back to str()")


def exact_fingerprint(obj: Any, n: int = 16) -> str:
    """Truncated hex fingerprint over the lossless encoding of ``obj``."""
    return exact_fingerprint_full(obj)[:n]


def exact_fingerprint_full(obj: Any) -> str:
    h = hashlib.sha256()
    h.update(FINGERPRINT_VERSION.encode("ascii"))
    h.update(b"\x00")
    h.update(_enc(obj))
    return h.hexdigest()


def envelope_fingerprint_inputs(peak: dict, hours: float, tolerance: float,
                                source: str) -> dict:
    """The SAME four inputs `envelope_digest` covers — nothing added, nothing
    dropped. Only the encoding differs, so a disagreement between the two is
    always a precision finding and never a scope difference."""
    missing = [p for p in PERIODS if p not in peak]
    if missing:
        raise NotFingerprintable(f"envelope is missing period(s): {missing}")
    extra = [p for p in peak if p not in PERIODS]
    if extra:
        raise NotFingerprintable(f"envelope carries unknown period(s): {extra}")
    if len(peak) == 1:
        raise NotFingerprintable("a one-entry mapping is a scalar cap in a "
                                 "dict costume; refused")
    return {"peak": {p: peak[p] for p in PERIODS}, "hours": hours,
            "tolerance": tolerance, "source": source}


def fingerprint_envelope_payload(payload: dict, n: int = 16) -> dict:
    """Fingerprint a `COMMON_RESOURCE_ENVELOPE.json`-shaped payload."""
    ins = envelope_fingerprint_inputs(
        peak={p: float(v) for p, v in payload["peak_fleet_by_period"].items()},
        hours=float(payload["weekday_revenue_vehicle_hours"]),
        tolerance=float(payload["budget_tolerance"]),
        source=str(payload["source"]))
    return {"fingerprint_version": FINGERPRINT_VERSION,
            "exact_envelope_fingerprint": exact_fingerprint(ins, n),
            "exact_envelope_fingerprint_full": exact_fingerprint_full(ins),
            "covers": ["peak_fleet_by_period (all six periods)",
                       "weekday_revenue_vehicle_hours", "budget_tolerance",
                       "source"],
            "identical_inputs_to": "envelope_digest",
            "differs_only_in": "lossless IEEE-754 encoding vs round(x, 9)"}


def _legacy_rounded_digest(peak: dict, hours: float, tolerance: float,
                           source: str, n: int = 16) -> str:
    """Reproduction of `envelope_digest`'s algorithm, for the self-test only.

    Mirrors `firewall.core.digest` (sorted-key compact JSON, sha256, first 16)
    applied to `exp4n_freeze_envelope.py`'s rounded payload. Used ONLY to
    demonstrate the collision this module fixes -- never as a checker."""
    blob = json.dumps({"peak": {p: round(peak[p], 9) for p in PERIODS},
                       "hours": round(hours, 9), "tolerance": tolerance,
                       "source": source}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()[:n]


# --------------------------------------------------------------------------
# self-test
# --------------------------------------------------------------------------
ACTUAL = {"early": 85.28208333333332, "am_peak": 162.00944444444443,
          "midday": 159.17277777777775, "pm_peak": 176.49305555555554,
          "evening": 140.19458333333336, "owl": 35.55736111111111}
# The two values transcribed wrongly during the freeze, verbatim from
# docs/ENVELOPE_DIGEST_INSUFFICIENCY.md.
HAND_TYPED = {**ACTUAL, "midday": 159.17277777777778,
              "evening": 140.19458333333333}
HOURS, TOL, SRC = 2517.1833333333334, 0.0, "reference_network_baseline_peak_by_period"


def _selftest() -> int:
    fails: list[str] = []

    def ok(name: str, cond: bool, detail: str = "") -> None:
        print(f"  {'PASS' if cond else 'FAIL'}  {name}"
              + (f"   {detail}" if detail else ""))
        if not cond:
            fails.append(name)

    def fp(peak, hours=HOURS, tol=TOL, src=SRC):
        return exact_fingerprint(envelope_fingerprint_inputs(peak, hours, tol, src))

    print("THE INCIDENT REPLAY -- the ULP pair that the rounded digest could not see")
    lg_a = _legacy_rounded_digest(ACTUAL, HOURS, TOL, SRC)
    lg_b = _legacy_rounded_digest(HAND_TYPED, HOURS, TOL, SRC)
    ok("actual and hand-typed differ in value", ACTUAL != HAND_TYPED,
       f"midday {ACTUAL['midday']!r} vs {HAND_TYPED['midday']!r}")
    ok("rounded envelope_digest COLLIDES on them (the defect)", lg_a == lg_b,
       f"{lg_a} == {lg_b}")
    ok("exact fingerprint SEPARATES them (the fix)", fp(ACTUAL) != fp(HAND_TYPED),
       f"{fp(ACTUAL)} != {fp(HAND_TYPED)}")

    print("determinism and order-independence")
    ok("stable across calls", fp(ACTUAL) == fp(ACTUAL))
    ok("insertion order cannot change it",
       fp(ACTUAL) == fp({p: ACTUAL[p] for p in reversed(PERIODS)}))
    ok("every period is covered", all(
        fp(ACTUAL) != fp({**ACTUAL, p: ACTUAL[p] + 1e-12}) for p in PERIODS))
    ok("hours are covered", fp(ACTUAL) != fp(ACTUAL, hours=HOURS + 1e-9))
    ok("tolerance is covered", fp(ACTUAL) != fp(ACTUAL, tol=1e-12))
    ok("source is covered", fp(ACTUAL) != fp(ACTUAL, src=SRC + "!"))

    print("smallest representable difference")
    one_ulp = math.nextafter(ACTUAL["midday"], math.inf)
    ok("1-ULP change is detected", fp(ACTUAL) != fp({**ACTUAL, "midday": one_ulp}),
       f"{ACTUAL['midday']!r} -> {one_ulp!r}")
    ok("1-ULP change is INVISIBLE to the rounded digest (why this exists)",
       _legacy_rounded_digest(ACTUAL, HOURS, TOL, SRC)
       == _legacy_rounded_digest({**ACTUAL, "midday": one_ulp}, HOURS, TOL, SRC))

    print("the declared encoding choices")
    ok("-0.0 separates from 0.0", exact_fingerprint(-0.0) != exact_fingerprint(0.0))
    ok("int 197 separates from float 197.0",
       exact_fingerprint(197) != exact_fingerprint(197.0))
    ok("True does not encode as int 1",
       exact_fingerprint(True) != exact_fingerprint(1))
    ok("inf encodes without loss", isinstance(exact_fingerprint(math.inf), str))
    ok("inf separates from -inf",
       exact_fingerprint(math.inf) != exact_fingerprint(-math.inf))
    ok("'1' separates from 1", exact_fingerprint("1") != exact_fingerprint(1))
    ok("[1,2] separates from [12]",
       exact_fingerprint([1, 2]) != exact_fingerprint([12]))
    ok("{'a':'bc'} separates from {'ab':'c'}",
       exact_fingerprint({"a": "bc"}) != exact_fingerprint({"ab": "c"}))

    print("refusals")
    for name, bad in (("NaN", float("nan")), ("set", {1, 2}),
                      ("object", object())):
        try:
            exact_fingerprint(bad)
            ok(f"{name} is refused", False, "it was encoded instead")
        except NotFingerprintable:
            ok(f"{name} is refused", True)
    try:
        envelope_fingerprint_inputs({"all": 197.0}, HOURS, TOL, SRC)
        ok("one-entry mapping is refused", False)
    except NotFingerprintable:
        ok("one-entry mapping is refused", True)
    try:
        envelope_fingerprint_inputs({p: ACTUAL[p] for p in PERIODS[:-1]},
                                    HOURS, TOL, SRC)
        ok("a missing period is refused", False)
    except NotFingerprintable:
        ok("a missing period is refused", True)

    print(f"\n{'ALL CHECKS PASS' if not fails else 'FAILURES: ' + ', '.join(fails)}")
    return 0 if not fails else 1


def _emit() -> int:
    """Record v1's reference values, INCLUDING EXP4N's envelope recomputed
    retrospectively from the lossless bit patterns already in its contract.

    Writes a NEW artifact. Touches no EXP4N file. The EXP4N number below is a
    reference for future comparison and is NOT a check on that run."""
    root = Path(__file__).resolve().parents[1]
    outdir = root / "outputs"
    env = json.loads((outdir / "exp4_normalized"
                      / "COMMON_RESOURCE_ENVELOPE.json").read_text())
    con = json.loads((outdir / "exp4_normalized"
                      / "EXP4N_PRODUCTION_CONTRACT.json").read_text())
    ex = con["exact_peak_envelope_used_by_this_run"]

    def unbits(rec: dict) -> float:
        return struct.unpack(">d", struct.pack(">Q", int(rec["int_bits"])))[0]

    peak_from_bits = {p: unbits(ex["values"][p]) for p in PERIODS}
    peak_from_artifact = {p: float(env["peak_fleet_by_period"][p]) for p in PERIODS}
    if peak_from_bits != peak_from_artifact:
        print("FATAL: the contract's lossless bit record and the frozen "
              "envelope artifact disagree; not writing anything.")
        for p in PERIODS:
            if peak_from_bits[p] != peak_from_artifact[p]:
                print(f"  {p}: bits {peak_from_bits[p]!r} "
                      f"artifact {peak_from_artifact[p]!r}")
        return 2

    fp = fingerprint_envelope_payload(env)
    payload = {
        "artifact": "ENVELOPE_FINGERPRINT_V1",
        "purpose": ("exact, bit-lossless envelope fingerprint for experiments "
                    "AFTER EXP4N; closes the deferred action in "
                    "docs/ENVELOPE_DIGEST_INSUFFICIENCY.md"),
        "authorized_by": "Ian, 2026-09-25, gated on EXP4N completing",
        "additive_only": True,
        "NOT": ("not retrofitted into the EXP4N contract; not a replacement "
                "for envelope_digest in any artifact already written; not "
                "usable to invalidate or re-verdict the completed EXP4N run, "
                "whose envelope identity was established before launch by "
                "bit-exact assertions against the frozen artifact and against "
                "the peak_caps of all 21 accepted calibration results"),
        "implementation": "scripts/envelope_fingerprint.py",
        "lives_outside_src_because": ("EXP4N pins src_cota_opt_content_digest "
                                      "= " + str(con["src_cota_opt_content_digest"])
                                      + " over src/cota_opt/**/*.py; adding a "
                                      "module there would move it"),
        **fp,
        "exp4n_envelope_reference": {
            "note": ("EXP4N's own envelope under the new fingerprint, computed "
                     "retrospectively from the int_bits already recorded in "
                     "its contract. A reference value for future comparison, "
                     "NOT a verdict on that run."),
            "envelope_digest_rounded_as_run": str(env["envelope_digest"]),
            "reconstructed_from_contract_bits_matches_artifact": True,
            "peak_repr": {p: repr(peak_from_bits[p]) for p in PERIODS},
            "hours_repr": repr(float(env["weekday_revenue_vehicle_hours"])),
        },
        "usage": ("from envelope_fingerprint import fingerprint_envelope_payload; "
                  "record BOTH envelope_digest and the exact fingerprint in any "
                  "new experiment's contract, and assert the envelope bit-exactly "
                  "against its frozen artifact as well -- a fingerprint proves "
                  "sameness, never correctness"),
    }
    p = outdir / "ENVELOPE_FINGERPRINT_V1.json"
    p.write_text(json.dumps(payload, indent=1))
    print(f"wrote {p}")
    print(f"  exact fingerprint      {payload['exact_envelope_fingerprint']}")
    print(f"  rounded digest as run  {env['envelope_digest']}")
    print("  reconstruction from the contract's int_bits matches the frozen "
          "artifact bit-for-bit in all six periods")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        raise SystemExit(_selftest())
    if "--emit" in sys.argv:
        raise SystemExit(_emit())
    print(__doc__)
    print("usage: envelope_fingerprint.py [--selftest | --emit]")
