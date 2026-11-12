"""Tests for tools/inspect_tank.py"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from workbook_loader import BreweryData, Tank, set_brewery_data
from tools.inspect_tank import inspect_tank


def _setup_tanks(tanks):
    data = BreweryData(demand_uplifts=[], packaging_lines=[], tanks=tanks)
    set_brewery_data(data)


def _make_tank(tank_id="MUC-T001", qc_status="Released", qc_note=""):
    return Tank(
        tank_id=tank_id, brewery="Munich", region="South", brand="Pils",
        ready_week=26, total_volume_hl=2000, allocated_volume_hl=800,
        free_volume_hl=1200, qc_status=qc_status, qc_note=qc_note,
    )


def test_inspect_tank_found():
    _setup_tanks([_make_tank("MUC-T001")])
    result = inspect_tank.invoke({"tank_id": "MUC-T001"})
    assert "MUC-T001" in result
    assert "Munich" in result
    assert "1200" in result
    assert "Released" in result


def test_inspect_tank_not_found():
    _setup_tanks([_make_tank("MUC-T001")])
    result = inspect_tank.invoke({"tank_id": "XXX-T999"})
    assert "not found" in result.lower()


def test_inspect_tank_case_insensitive():
    _setup_tanks([_make_tank("MUC-T001")])
    result = inspect_tank.invoke({"tank_id": "muc-t001"})
    assert "MUC-T001" in result


def test_inspect_tank_hold_includes_qc_note():
    _setup_tanks([_make_tank("NUE-T006", qc_status="Hold", qc_note="Diacetyl above threshold")])
    result = inspect_tank.invoke({"tank_id": "NUE-T006"})
    assert "Hold" in result
    assert "Diacetyl above threshold" in result


def test_inspect_tank_shows_all_key_fields():
    _setup_tanks([_make_tank("MUC-T001")])
    result = inspect_tank.invoke({"tank_id": "MUC-T001"})
    assert "Free Volume" in result
    assert "Allocated Volume" in result
    assert "Ready Week" in result
