"""Tests for tools/check_coverage.py"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from workbook_loader import BreweryData, Tank, PackagingLine, set_brewery_data
from tools.check_coverage import check_coverage


def _setup(tanks, packaging_lines):
    data = BreweryData(demand_uplifts=[], packaging_lines=packaging_lines, tanks=tanks)
    set_brewery_data(data)


def _released_tank(tank_id, brewery, brand, ready_week, free_volume_hl):
    return Tank(
        tank_id=tank_id, brewery=brewery, region="South", brand=brand,
        ready_week=ready_week, total_volume_hl=free_volume_hl + 500,
        allocated_volume_hl=500, free_volume_hl=free_volume_hl,
        qc_status="Released", qc_note="",
    )


def _line(brewery, capacity):
    return PackagingLine(line_id="L01", brewery=brewery, format="bottle",
                          free_capacity_hl_per_week=capacity)


def test_check_coverage_yes():
    _setup(
        tanks=[_released_tank("MUC-T001", "Munich", "Pils", 26, 1500)],
        packaging_lines=[_line("Munich", 2000)],
    )
    result = check_coverage.invoke({"region": "South", "brand": "Pils",
                                     "demand_hl": 1000, "week_start": 27, "week_end": 28})
    assert "Yes" in result
    assert "MUC-T001" in result


def test_check_coverage_no():
    _setup(tanks=[], packaging_lines=[_line("Munich", 2000)])
    result = check_coverage.invoke({"region": "South", "brand": "Pils",
                                     "demand_hl": 1000, "week_start": 27, "week_end": 28})
    assert "No" in result


def test_check_coverage_partially():
    _setup(
        tanks=[_released_tank("MUC-T001", "Munich", "Pils", 26, 600)],
        packaging_lines=[_line("Munich", 2000)],
    )
    result = check_coverage.invoke({"region": "South", "brand": "Pils",
                                     "demand_hl": 1000, "week_start": 27, "week_end": 28})
    assert "Partially" in result


def test_check_coverage_includes_recommendation():
    _setup(
        tanks=[_released_tank("MUC-T001", "Munich", "Pils", 26, 1500)],
        packaging_lines=[_line("Munich", 2000)],
    )
    result = check_coverage.invoke({"region": "South", "brand": "Pils",
                                     "demand_hl": 1000, "week_start": 27, "week_end": 28})
    assert "Recommendation" in result


def test_check_coverage_unknown_region():
    _setup(tanks=[], packaging_lines=[])
    result = check_coverage.invoke({"region": "North", "brand": "Pils",
                                     "demand_hl": 1000, "week_start": 27, "week_end": 28})
    assert "failed" in result.lower() or "unknown" in result.lower()
