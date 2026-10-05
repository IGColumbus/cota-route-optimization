"""The envelope units sidecar classifies every numeric field, and labels cannot
present a proxy as vehicles (or a physical count as a proxy)."""
from __future__ import annotations

import json

import pytest

from cota_release import units


def test_every_numeric_envelope_field_is_classified():
    side = units.sidecar()
    for artifact, fields in side["fields"].items():
        data = json.loads((units.ROOT / artifact).read_text())
        leaves = units.leaf_fields(data)
        missing = sorted(set(leaves) - set(fields))
        assert not missing, f"{artifact}: unclassified numeric fields {missing}"
        for name, entry in fields.items():
            assert entry["class"] in side["classes"], (artifact, name)
            assert entry.get("provenance"), (artifact, name)


def test_class_labels_pass_their_own_check():
    for cls in (units.PHYSICAL, units.PROXY):
        units.check_label(units.class_label(cls), cls)


@pytest.mark.parametrize("text", ["peak vehicles", "% of peak fleet", "buses at peak"])
def test_proxy_presented_as_vehicles_fails(text):
    with pytest.raises(ValueError):
        units.check_label(text, units.PROXY)


def test_physical_presented_as_proxy_fails():
    with pytest.raises(ValueError):
        units.check_label("peak proxy units", units.PHYSICAL)


def test_known_traps_are_classified_correctly():
    # the frozen field names say "fleet"/"vehicles" for both kinds of quantity
    assert units.field_class("outputs/CANONICAL_ENVELOPE.json", "peak_vehicles") == units.PHYSICAL
    assert units.field_class("outputs/exp4_normalized/COMMON_RESOURCE_ENVELOPE.json",
                             "peak_fleet_by_period.pm_peak") == units.PROXY
    assert units.field_class(
        "outputs/CANONICAL_ENVELOPE.json",
        "NOT_THE_CAP.frequency_model_peak_concurrency.value_on_baseline_pm_peak") == units.PROXY


def test_figure_tooling_takes_labels_from_sidecar():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "make_report_figures", units.ROOT / "scripts" / "make_report_figures.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.PEAK_AXIS_LABEL == units.display_label("resource_curve_peak_axis")
    assert mod.HOURS_AXIS_LABEL == units.display_label("resource_curve_hours_axis")
