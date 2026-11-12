"""Tests for tools/list_pending_tanks.py"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from workbook_loader import BreweryData, Tank, set_brewery_data
from tools.list_pending_tanks import list_pending_tanks


def _setup(tanks):
    data = BreweryData(demand_uplifts=[], packaging_lines=[], tanks=tanks)
    set_brewery_data(data)


def _tank(tank_id, brewery, brand, qc_status, free_volume_hl, ready_week=27, qc_note=""):
    return Tank(
        tank_id=tank_id, brewery=brewery, region="South", brand=brand,
        ready_week=ready_week, total_volume_hl=free_volume_hl + 500,
        allocated_volume_hl=500, free_volume_hl=free_volume_hl,
        qc_status=qc_status, qc_note=qc_note,
    )


def test_list_pending_tanks_found():
    _setup([
        _tank("MUC-T003", "Munich", "Pils", "Pending", 1000, qc_note="Lab check"),
    ])
    result = list_pending_tanks.invoke({"region": "South", "brand": "Pils"})
    assert "MUC-T003" in result
    assert "1000" in result


def test_list_pending_tanks_none_found():
    _setup([
        _tank("MUC-T001", "Munich", "Pils", "Released", 1200),
    ])
    result = list_pending_tanks.invoke({"region": "South", "brand": "Pils"})
    assert "No Pending tanks" in result


def test_list_pending_tanks_ranked_by_volume():
    _setup([
        _tank("MUC-T003", "Munich", "Pils", "Pending", 800),
        _tank("NUE-T002", "Nuremberg", "Pils", "Pending", 1200),
    ])
    result = list_pending_tanks.invoke({"region": "South", "brand": "Pils"})
    # NUE-T002 (1200 hl) should appear before MUC-T003 (800 hl)
    assert result.index("NUE-T002") < result.index("MUC-T003")


def test_list_pending_tanks_unknown_region():
    _setup([])
    result = list_pending_tanks.invoke({"region": "North", "brand": "Pils"})
    assert "Unknown region" in result


def test_list_pending_tanks_cross_region_excluded():
    _setup([
        _tank("DOR-T003", "Dortmund", "Pils", "Pending", 1500),
    ])
    # Asking South — Dortmund tank should not appear
    result = list_pending_tanks.invoke({"region": "South", "brand": "Pils"})
    assert "No Pending tanks" in result
